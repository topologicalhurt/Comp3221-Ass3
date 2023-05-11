import contextlib
import socket
import threading
from queue import Queue
from typing import Callable, Optional, List
import select

from conf import Config


def starts_thread(func: Callable):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        t.join()

    return wrapper


@contextlib.contextmanager
def tcp_make_nattempts(host: str, ports: List[int]) -> List[socket.socket]:
    socks = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(False)
        s.connect((host, p))
        socks.append(s)

    poller = select.poll()
    for s in socks:
        poller.register(s, select.POLLRDHUP)
    events = poller.poll(Config.INIT_NODE_CONN_TIMEOUT)
    for sock, sock_bc, e in zip(socks, events):
        with sock:
            # TODO: should attempt to reconstruct the socket once more
            if e & select.POLLRDHUP:
                raise TimeoutError(f'No socket could be connected to on the port: {sock.getsockname()}')
            yield sock


def tcp_broadcaster(host: str, ports: List[int]):
    def wrapper(func: Callable):
        def inner_wrapper(*args, **kwargs):
            with tcp_make_nattempts(host, ports) as s:
                s.sendall(func(*args, **kwargs))
        return inner_wrapper
    return wrapper


@starts_thread
def start_soc_listener(host: str, port: int, buffer: Queue, sem: Optional[threading.Condition] = None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        # If a semaphore is provided then all listening threads continue once connection binds
        if sem:
            with sem:
                sem.notify_all()
        while True:
            conn, addr = s.accept()
            with conn:
                # Exhaust the buffer 1KB at a time
                payload = b''
                while True:
                    buf = conn.recv(1024)
                    if not buf:
                        break
                    payload += buf
                # Threadsafe because buffer enters a mutex
                buffer.put_nowait(payload)
