import argparse
import asyncio
import datetime
import heapq
import logging
import os
import re
import socket
import sys
import threading
from queue import Queue
from typing import Callable, Optional, List
import select

from conf import CONFIG
from consts import Colors

if __debug__:
    soc_listener_threads = []
else:
    soc_listener_threads = None

__loop = asyncio.get_event_loop()
__lock = threading.Lock()

__log_format = re.compile(r'((?:[01][0-9])|(?:2[0-3]))((?:[012345][0-9]){2})')


def start_threads(threads: List, n_threads=1, join=False):
    def inner_decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_n_threads(func, threads, n_threads, join, *args, **kwargs)

        return wrapper

    return inner_decorator


def start_n_threads(func: Callable, threads: List, n_threads=1, join=False, *args, **kwargs):
    if threads is None:
        threads = []
    for _ in range(n_threads):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        threads.append(t)
    if join:
        for t in threads:
            t.join()


def debug(*colors):
    def inner_decorator(func: Callable):
        def wrapper(*args, **kwargs):
            if __debug__:
                return ''.join(map(Colors.str_to_c, colors)) \
                    + func(*args, **kwargs) \
                    + str(Colors.END.value)

        return wrapper

    return inner_decorator


async def tcp_make_nattempts(hosts: List[str], ports: List[int], buffer_peers):
    socks = []
    for h, p in zip(hosts, ports):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Re-use address (potentially reconstruct the socket)
        s.setblocking(False)  # Needs to be non-blocking for async io
        s.connect_ex((h, p))
        socks.append(s)

    # Wait for spec. time (see: conf.json) for port to begin listening if buffering defined
    if buffer_peers:
        await asyncio.sleep(CONFIG.INIT_NODE_WAIT_BUF)

    err = None
    for i in range(CONFIG.INIT_NODE_N_RECONSTRUCTS):
        # For asynchronous reads of all peers (use a single-thread to monitor all sockets)
        _, rtw, err = select.select([], socks, socks, CONFIG.INIT_NODE_CONN_TIMEOUT)

        # For all ready to write socket pipes, yield the socket
        for s in rtw:
            with s:
                yield s
        if not err:
            break  # Done if no errors remain

        # Reconstruct socket pipes for reconnection attempt
        for e in err:
            # TODO: should attempt to reconstruct the socket once more
            await asyncio.sleep(CONFIG.INIT_NODE_RECONSTRUCT_WAIT_BUF)
    else:
        for e in err:
            with e:
                raise TimeoutError(f'The port located @ {e.getsockname()} failed to connect')
            yield None


# TODO: self as positional argument & hardcoded attrs are ugly. Fix.
def tcp_broadcaster(buffer_peers=True):
    def inner_decorator(func: Callable):
        def wrapper(*args, **kwargs):
            async def inner_wrapper(*args, **kwargs):
                async for s in tcp_make_nattempts([n.host for n in args[0].peers],
                                                  [n.port for n in args[0].peers],
                                                  buffer_peers):
                    payload = func(*args, **kwargs)
                    if s and payload:
                        s.sendall(payload.encode())

            # Only one event loop can be accessed at any given time.
            # That is, only one node can poll all it's peers at any given time
            # which makes perfect sense
            with __lock:
                return __loop.run_until_complete(inner_wrapper(*args, **kwargs))

        return wrapper

    return inner_decorator


@start_threads(soc_listener_threads)
def start_soc_listener(host: str, port: int, buffer: Queue, sem: Optional[threading.Event] = None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        # If a semaphore is provided then all listening threads continue once connection binds
        if sem:
            sem.set()
        while True:
            conn, addr = s.accept()
            with conn:
                # Exhaust the buffer
                payload = b''
                while True:
                    buf = conn.recv(CONFIG.RECV_PIPE_BUF_SIZE)
                    if not buf:
                        break
                    payload += buf
                # Threadsafe because buffer enters a mutex
                buffer.put(payload)
                if __debug__:
                    sys.stdout.write(f'{host}:{port} received the following -> "{buffer.get().decode()}"\n')
                    sys.stdout.flush()


def cleanup_logs():
    """Keep the n (CONFIG.N_CONFIGS_TO_KEEP) most recent log files
    Warn about any log files that are incorrectly formatted
    """
    heap = []
    heapq.heapify(heap)
    for f in os.listdir():
        if f.endswith('.log'):
            fname_pivot = f.index('_')
            re_split = re.split(__log_format, f[fname_pivot + 1:])
            if len(re_split) != 4 or not re.fullmatch(__log_format, f'{"".join(re_split[1:-1])}'):
                logging.warning(f'log file w/ name {f} is not recognised as a valid date')
                continue
            dt = 10 ** 6 * int(f[:fname_pivot]) + int(f[fname_pivot + 1:f.index('.')])
            heapq.heappush(heap, (-dt, f))
    i = 0
    while heap:
        i += 1
        if i > CONFIG.N_CONFIGS_TO_KEEP:
            os.remove(heapq.heappop(heap)[1])
        else:
            heapq.heappop(heap)


# Full credit to https://stackoverflow.com/a/66209331
class LoggerWriter:
    def __init__(self, logger):
        self.logger = logger
        self.buf = []

    def write(self, msg):
        if msg.endswith('\n'):
            self.buf.append(msg[:-1])
            self.logger(''.join(self.buf))
            self.buf = []
        else:
            self.buf.append(msg)

    def flush(self):
        pass


# Borrowed from 510427586's contribution to ass2
def verify_flag(arg: str) -> bool:
    arg = arg.lower()
    match arg:
        case 'true' | '1':
            return True
        case 'false' | '0':
            return False
        case _:
            raise argparse.ArgumentTypeError('A flag must be one of: [true, false, 1, 0]')


def debug_msg(msg: str):
    @debug('red', 'italic', 'faint')
    def wrapper(msg: str) -> str:
        return msg
    out = wrapper(msg)
    if out:
        sys.stdout.write(wrapper(msg) + '\n')
