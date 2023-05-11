from blockchain import *
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
import threading
from utils import start_soc_listener, tcp_broadcaster
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

    def __init__(self, host, port, f) -> None:
        self.blockchain = Blockchain()
        self.host = host
        self.port = port
        self.requests = Queue()  # Keep track of requests in threadsafe queue
        self.peers = set()
        self.started = False

    def start(self):
        started_soc = threading.Condition()
        start_soc_listener(self.host, self.port, self.requests, started_soc)
        # Wait for the connection to bind
        with started_soc:
            started_soc.wait()
        # These are not atomic so starting nodes in parallel is not currently supported
        ServerRunner.n_peers += 1
        self.started = True

    def stop(self):
        if not self.started:
            raise TypeError('Operation stop not supported on an un-started server instance')


    @tcp_broadcaster(self.host, [n.port for n in self.peers])
    def handshake(self):
        pass

    def append(self, remote_node: RemoteNode):
        if not self.started:
            raise TypeError('Operation append not supported on an un-started server instance')
        elif remote_node in self.peers:
            raise ValueError('Cannot add the same peer more than once per server instance')

        self.peers.add(remote_node)
        n_seen_peers = len(self.peers)

        if n_seen_peers == ServerRunner.n_peers - 1:


            # conn_barrier = threading.Barrier(ServerRunner.n_peers)
            # with conn_barrier:
            #     conn_barrier.wait()

        elif n_seen_peers >= ServerRunner.n_peers:
            raise ValueError('The number of encountered peers is greater than the number of started peers')

