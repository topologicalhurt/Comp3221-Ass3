from blockchain import *
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

def make_transaction(message: str, private_key: ed25519.Ed25519PrivateKey, nonce: int):
	pass

class RemoteNode():
	def __init__(self, host, port) -> None:
		pass

	def transaction(self, transaction):
		pass

class ServerRunner():
	def __init__(self, host, port, f) -> None:
		self.blockchain = Blockchain()

	def start(self):
		pass

	def stop(self):
		pass

	def append(self, remote_node: RemoteNode):
		pass
