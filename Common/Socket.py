from socket import socket
from math import ceil
from struct import *

ChunkSize = 1024  # in bytes

'''
All send functions return False on success, True on fail.
'''


def SendInt(sock: socket, i: int) -> bool:
    return not (sock.sendall(pack('!i', i)) is None)


def _sendChunk(sock: socket, chunk: bytes) -> bool:
    return not (sock.sendall(chunk) is None)


def _sendSizedChunk(sock: socket, chunk: bytes) -> bool:
    if SendInt(sock, len(chunk)):
        return True
    return not (sock.sendall(chunk) is None)


def SendBytes(sock: socket, bts: bytes) -> bool:
    n = ceil(len(bts) / ChunkSize)
    if n <= 0: return False  # False, because no send error
    # Send number of chunks
    if SendInt(sock, n):
        return True
    # Send first n - 1 chunks
    for i in range(n - 1):
        this = bts[i * ChunkSize:(i + 1) * ChunkSize]
        if _sendChunk(sock, this):
            return True
    # Send last chunk
    last = bts[(n - 1) * ChunkSize:]
    if _sendSizedChunk(sock, last):
        return True
    return False


def SendStr(sock: socket, s: str) -> bool:
    return SendBytes(sock, s.encode())


class RecvError(Exception):
    def __init__(self, mes: str = 'No bytes received'):
        self.mes = mes

    def __str__(self):
        return self.mes


def _checkBytes(bts: bytes):
    if not bts:
        raise RecvError()


def RecvInt(sock: socket) -> int:
    result = sock.recv(4)
    _checkBytes(result)
    return unpack('!i', result)[0]


def RecvChunk(sock: socket) -> bytes:
    result = sock.recv(ChunkSize)
    _checkBytes(result)
    return result


def RecvSizedChunk(sock: socket) -> bytes:
    size = RecvInt(sock)
    result = sock.recv(size)
    _checkBytes(result)
    return result


def RecvBytes(sock: socket) -> bytes:
    n = RecvInt(sock)
    result = b''
    for i in range(n - 1):
        result += RecvChunk(sock)
    result += RecvSizedChunk(sock)
    return result


def RecvStr(sock: socket) -> str:
    return RecvBytes(sock).decode()
