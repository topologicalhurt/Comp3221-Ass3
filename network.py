import socket
import struct


def soc_recv_exact(sock: socket.socket, msg_len):
    chunks = []
    bytes_recd = 0
    while bytes_recd < msg_len:
        chunk = sock.recv(min(msg_len - bytes_recd, 2048))
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    return b''.join(chunks)


def soc_send_exact(sock: socket.socket, msg: bytes):
    total_sent = 0
    while total_sent < len(msg):
        sent = sock.send(msg[total_sent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        total_sent = total_sent + sent


def soc_recv_prefixed(sock: socket.socket):
    size_bytes = soc_recv_exact(sock, 2)
    size = struct.unpack("!H", size_bytes)[0]
    if size == 0:
        raise RuntimeError("empty message")
    if size > 65535 - 2:
        raise RuntimeError("message too large")
    return soc_recv_exact(sock, size)


def soc_send_prefixed(sock: socket.socket, msg: bytes):
    size = len(msg)
    if size == 0:
        raise RuntimeError("empty message")
    if size > 65535 - 2:
        raise RuntimeError("message too large")
    size_bytes = struct.pack("!H", size)
    soc_send_exact(sock, size_bytes + msg)
