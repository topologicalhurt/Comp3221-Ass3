from blockchain import *
from _thread import *
import _thread
import threading
import socket

import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

IP = "127.0.0.1"


def make_transaction(message: str, private_key: ed25519.Ed25519PrivateKey, nonce: int):
	pass


def on_new_client(c, addr, server):
	# TODO: figure this out
	# this whole function is designed to be run as a thread
	# pretty much just constantly looks for data, we will decide what to do with it later

	# nvm i dont think append is called here, it is called in setup elsewhere
	while True:
		print('Connection from', c.getsockname())
		data_rev = c.recv(1024)
		if not data_rev:
			print("didn't get data")
			break
		print(data_rev.decode('utf-8'))
		data = bytes('yo', encoding='utf-8')
		c.sendall(data)
	c.close()


class RemoteNode():
	def __init__(self, host, port) -> None:
		self.host = host
		self.port = port


	def transaction(self, transaction):
		# wtf transaction is supposed to do, idk i will keep this function here for now tho
		pass


class ServerRunner():
	def __init__(self, host, port, f) -> None:
		self.port = port
		self.host = host
		self.f = f
		self.blockchain = Blockchain()
		self.RNList = []

	def start(self):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				print("Server host names: ", IP, "Port: ", self.port)
				s.bind((IP, self.port))  # Bind to the port
				s.listen(5)
				while True:
					c, addr = s.accept()
					_thread.start_new_thread(on_new_client, (c, addr, self))
				s.close()
		except:
			print("Can't connect to the Socket")

	def stop(self):
		pass

	def append(self, remote_node: RemoteNode):
		# I assume u add the remote nodes to a list
		self.RNList.append(remote_node)
