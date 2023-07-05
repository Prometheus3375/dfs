import functools
from math import ceil
from socket import socket, error as _error, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import pack, unpack, calcsize

from Common.Misc import EnumCode, MyError

Errors = EnumCode()
Error_ConnectFailed = Errors('Connection to the remote host has failed')
Error_SocketClosed = Errors('The remote host has closed the connection')
Error_Other = Errors.top + 1

ChunkSize = 1024  # in bytes
IntFormat = '!i'
IntSize = calcsize(IntFormat)


class SocketError(MyError):
    def __init__(self, err_code: int, msg: str = ''):
        super().__init__(Errors, err_code, msg)


def connect(func):
    @functools.wraps(func)
    def wrapper(host: tuple, *args):
        with socket(AF_INET, SOCK_STREAM) as sock:
            try:
                sock.connect(host)
            except _error:
                raise SocketError(Error_ConnectFailed)
            wrapper.sock = sock
            return func(sock, *args)

    return wrapper


def BindAndListen(name: str, port: int) -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((name, port))
    sock.listen()
    return sock


def Accept(sock: socket) -> tuple:
    try:
        return sock.accept()
    except _error as e:
        raise SocketError(Error_Other, str(e))


def _sendall(sock: socket, bts: bytes):
    try:
        result = sock.sendall(bts)
    except _error as e:
        raise SocketError(Error_Other, str(e))
    if result is not None:
        raise SocketError(Error_SocketClosed)


def SendInt(sock: socket, i: int):
    _sendall(sock, pack(IntFormat, i))


def _sendChunk(sock: socket, chunk: bytes):
    _sendall(sock, chunk)


def _sendSizedChunk(sock: socket, chunk: bytes):
    SendInt(sock, len(chunk))
    _sendChunk(sock, chunk)


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
    try:
        result = sock.recv(bufsize)
    except _error as e:
        raise SocketError(Error_Other, str(e))
    if result:
        return result
    raise SocketError(Error_SocketClosed)


def RecvInt(sock: socket) -> int:
    result = _recv(sock, IntSize)
    return unpack(IntFormat, result)[0]


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
