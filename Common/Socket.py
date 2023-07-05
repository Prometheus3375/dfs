import functools
from math import ceil
from socket import socket, AF_INET, SOCK_STREAM, error as _error
from struct import *

from Common.Misc import Enum
from Common.Misc import MyException

Errors = Enum()
Error_Other = Errors.new()
Error_Connect = Errors.new()
Error_Send = Errors.new()
Error_Recv = Errors.new()


class SocketError(MyException):
    def __init__(self, mes: str = '', code: int = Error_Other):
        super(SocketError, self).__init__(mes)
        self.err = code


ChunkSize = 1024  # in bytes


def connect(func):
    @functools.wraps(func)
    def wrapper(host: tuple, *args):
        with socket(AF_INET, SOCK_STREAM) as sock:
            try:
                sock.connect(host)
            except _error:
                raise SocketError('Failed to connect to %s:%d' % host, Error_Connect)
            wrapper.sock = sock
            return func(sock, *args)

    return wrapper


def _sendall(sock: socket, bts: bytes):
    if not (sock.sendall(bts) is None):
        raise SocketError('Send to %s:%d failed' % sock.getpeername(), Error_Send)


def SendInt(sock: socket, i: int):
    _sendall(sock, pack('!i', i))


def _sendChunk(sock: socket, chunk: bytes):
    _sendall(sock, chunk)


def SendChunk(sock: socket, chunk: bytes):
    if len(chunk) == ChunkSize:
        _sendChunk(sock, chunk)
    raise SocketError('Size of passed chunk must equal %d, '
                      'for bigger sizes use SendBytes, for smaller use SendSizedChunk' % ChunkSize)


def _sendSizedChunk(sock: socket, chunk: bytes):
    SendInt(sock, len(chunk))
    _sendChunk(sock, chunk)


def SendSizedChunk(sock: socket, chunk: bytes):
    if len(chunk) <= ChunkSize:
        _sendSizedChunk(sock, chunk)
    raise SocketError('Size of passed chunk must be not bigger than %d, '
                      'for bigger sizes use SendBytes' % ChunkSize)


def SendBytes(sock: socket, bts: bytes):
    n = ceil(len(bts) / ChunkSize)
    # Send number of chunks
    SendInt(sock, n)
    if n > 0:
        # Send first n - 1 chunks
        for i in range(n - 1):
            this = bts[i * ChunkSize:(i + 1) * ChunkSize]
            _sendChunk(sock, this)
        # Send last chunk
        last = bts[(n - 1) * ChunkSize:]
        _sendSizedChunk(sock, last)


def SendStr(sock: socket, s: str):
    return SendBytes(sock, s.encode())


def _recv(sock: socket, bufsize: int) -> bytes:
    result = sock.recv(bufsize)
    if not result:
        raise SocketError('No bytes received from %s:%d' % sock.getpeername(), Error_Recv)
    return result


def RecvInt(sock: socket) -> int:
    result = _recv(sock, 4)
    return unpack('!i', result)[0]


def RecvChunk(sock: socket) -> bytes:
    return _recv(sock, ChunkSize)


def RecvSizedChunk(sock: socket) -> bytes:
    size = RecvInt(sock)
    return _recv(sock, size)


def RecvBytes(sock: socket) -> bytes:
    n = RecvInt(sock)
    result = b''
    if n > 0:
        for i in range(n - 1):
            result += RecvChunk(sock)
        result += RecvSizedChunk(sock)
    return result


def RecvStr(sock: socket) -> str:
    return RecvBytes(sock).decode()
