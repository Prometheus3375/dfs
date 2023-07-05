import functools
from ipaddress import IPv4Address, AddressValueError, IPv4Network
from math import ceil
from socket import socket, error as _error, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, gethostbyname
from struct import pack, unpack, calcsize

from Common.Misc import EnumCode, MyError

Errors = EnumCode()
Error_ConnectFailed = Errors('Connection to the remote host has failed')
Error_SocketClosed = Errors('The remote host has closed the connection')
Error_Other = Errors.top + 1

ChunkSize = 1024  # in bytes
SocketTimeout = 1800  # in seconds

UByteFormat = '!B'
UByteSize = calcsize(UByteFormat)
IntFormat = '!i'
IntSize = calcsize(IntFormat)
ULongFormat = '!Q'
ULongSize = calcsize(ULongFormat)


class SocketError(MyError):
    def __init__(self, err_code: int, msg: str = ''):
        super().__init__(Errors, err_code, msg)


def connection(ip: str = None, port: int = None, timeout: float = SocketTimeout):
    def _connect(func):
        def wrapper(host: tuple, *args):
            with socket(AF_INET, SOCK_STREAM) as sock:
                try:
                    sock.settimeout(timeout)
                    sock.connect(host)
                except _error:
                    raise SocketError(Error_ConnectFailed)
                return func(sock, *args)

        if ip is None and port is None:
            @functools.wraps(func)
            def w(host: tuple, *args):
                return wrapper(host, *args)

            return w
        if ip is None:
            @functools.wraps(func)
            def w(ip: str, *args):
                return wrapper((ip, port), *args)

            return w
        if port is None:
            @functools.wraps(func)
            def w(port: int, *args):
                return wrapper((ip, port), *args)

            return w

        @functools.wraps(func)
        def w(*args):
            return wrapper((ip, port), *args)

        return w

    return _connect


def CheckNet(net: str) -> str:
    try:
        IPv4Network(net)
        return ''
    except AddressValueError as e:
        return str(e)


def CheckIP(ip: str) -> str:
    try:
        IPv4Address(ip)
    except AddressValueError:
        try:
            ip = gethostbyname(ip)
        except _error:
            return ''
    return ip


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


def SendUByte(sock: socket, i: int):
    _sendall(sock, pack(UByteFormat, i))


def SendInt(sock: socket, i: int):
    _sendall(sock, pack(IntFormat, i))


def SendULong(sock: socket, i: int):
    _sendall(sock, pack(ULongFormat, i))


def _sendChunk(sock: socket, chunk: bytes):
    _sendall(sock, chunk)


def _sendSizedChunk(sock: socket, chunk: bytes):
    SendInt(sock, len(chunk))
    _sendChunk(sock, chunk)


def SendBytes(sock: socket, bts: bytes):
    n = len(bts)
    # Send size
    SendULong(sock, n)
    if n > 0:
        # Get number of chunks
        chunks = ceil(n / ChunkSize)
        # Send all chunks
        for i in range(chunks):
            this = bts[i * ChunkSize:(i + 1) * ChunkSize]
            _sendChunk(sock, this)


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


def RecvUByte(sock: socket) -> int:
    result = _recv(sock, UByteSize)
    return unpack(UByteFormat, result)[0]


def RecvInt(sock: socket) -> int:
    result = _recv(sock, IntSize)
    return unpack(IntFormat, result)[0]


def RecvULong(sock: socket) -> int:
    result = _recv(sock, ULongSize)
    return unpack(ULongFormat, result)[0]


def RecvChunk(sock: socket) -> bytes:
    return _recv(sock, ChunkSize)


def RecvSizedChunk(sock: socket) -> bytes:
    size = RecvInt(sock)
    return _recv(sock, size)


def RecvBytes(sock: socket) -> bytes:
    # Get number of bytes
    n = RecvULong(sock)
    result = b''
    if n > 0:
        # Find chunk number
        chunks = ceil(n / ChunkSize)
        # Get all chunk except last
        for i in range(chunks - 1):
            result += RecvChunk(sock)
        # Last chunk will have different size, calculate it
        result += _recv(sock, n - (chunks - 1) * ChunkSize)
    return result


def RecvStr(sock: socket) -> str:
    return RecvBytes(sock).decode()
