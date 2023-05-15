import asyncio
import sys

from blockchain import *
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
import threading
from utils import start_soc_listener, tcp_broadcaster, debug, start_n_threads, debug_msg
from queue import Queue


def make_transaction(message: str, private_key: ed25519.Ed25519PrivateKey, nonce: int):
    pass


class RemoteNode:
    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port

    def transaction(self, transaction):
        pass

    def __wait_on_transaction(self):
        pass

    def __make_block_proposal(self):
        pass

    def __sync_consensus_prot(self):
        pass


class ServerRunner:
    n_peers = 0
    peer_threads = []
    conn_barrier = None
    lock = threading.Lock()
    start_event = threading.Event()

    def __init__(self, host, port, f) -> None:
        self.blockchain = Blockchain()
        self.host = host
        self.port = port
        self.requests = Queue()  # Keep track of requests in threadsafe queue
        self.peers = set()
        self.started = False
        self.ready_event = threading.Event()

    def start(self):
        started_soc = threading.Event()
        start_soc_listener(self.host, self.port, self.requests, sem=started_soc)  # Starts a new listener thread

        # Wait for the connection to bind
        started_soc.wait()

        # These are not atomic because starting nodes in parallel is not supported
        ServerRunner.n_peers += 1
        self.started = True
        start_n_threads(self.__client_thread, ServerRunner.peer_threads,
                        join=False)

    def stop(self):
        if not self.started:
            raise TypeError('Operation stop not supported on an un-started server instance')
        for t in ServerRunner.peer_threads:
            t.join()
        asyncio.get_event_loop().stop()

    def append(self, remote_node: RemoteNode):
        """NOT THREAD-SAFE: THE OFFICIAL USAGE EXAMPLE REQUIRES THAT APPEND BE RAN AFTER START
        (I.E SEQUENTIALLY). A THREAD-ORIENTATED OR ASYNC APPROACH COULD BE EASILY ACHIEVED BY REMOVING
        REFs TO STATIC ATTR's (E.G start_finished, n_peers) BUT THIS WOULD REQUIRE THE USAGE
        DESIGN PATTERN TO CHANGE. OVERALL, THE INTENDED DESIGN IS PRIORITISED EVEN IF IT IS
        BAD PRACTICE
        """

        if not ServerRunner.start_event.is_set():
            ServerRunner.conn_barrier = threading.Barrier(ServerRunner.n_peers)
            ServerRunner.start_event.set()

        if not self.started:
            raise RuntimeError(
                TypeError('Operation append not supported on an un-started server instance')
            )
        elif remote_node in self.peers:
            raise RuntimeError(
                ValueError('Cannot add the same peer more than once per server instance')
            )

        # This is criminally ugly/bad event logic but again, adhering to the design
        self.peers.add(remote_node)
        n_seen_peers = len(self.peers)
        if n_seen_peers == ServerRunner.n_peers - 1:
            # Send a handshake in debug mode to verify all the peers are connected properly
            self.__send_handshake_msg()
            self.ready_event.set()
        elif n_seen_peers >= ServerRunner.n_peers:
            raise RuntimeError(
                ValueError('The number of encountered peers is greater than the number of started peers')
            )

    @tcp_broadcaster(buffer_peers=True)
    @debug('red', 'italic')
    def __send_handshake_msg(self):
        return f'Initial handshake completed {self.host}:{self.port}'

    @tcp_broadcaster(buffer_peers=True)
    @debug('light_red', 'italic')
    def __send_handshake_msg2(self):
        return f'All peer transaction pools in agreement {self.host}:{self.port}'

    def __client_thread(self):
        """A 'separate thread should be created for each connected client' (P3, Sec2.2)
        This thread is created, in addition to a TCP listener thread, for each client
        """

        # Happens after start
        ServerRunner.start_event.wait()
        debug_msg(f'Start done for {self.host}:{self.port}')

        # Happens after all appends are done (I.E all peer transaction pools visible)
        self.ready_event.wait()
        self.ready_event.clear()
        debug_msg(f'Handshake done for {self.host}:{self.port}')
        tid = ServerRunner.conn_barrier.wait()
        if tid == 0:
            ServerRunner.conn_barrier.reset()
            debug_msg('All handshakes done')

        # Symbolic acknowledgement that all peers are in agreement of each other
        self.__send_handshake_msg2()
