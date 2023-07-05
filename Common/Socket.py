import functools
from ipaddress import IPv4Address, AddressValueError, IPv4Network
from math import ceil, floor
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
    size = len(bts)
    sent = 0
    try:
        while sent < size:
            result = sock.send(bts[sent:])
            if result == 0:
                raise SocketError(Error_SocketClosed)
            sent += result
    except _error as e:
        raise SocketError(Error_Other, str(e))


def _recv(sock: socket, bufsize: int) -> bytes:
    try:
        result = sock.recv(bufsize)
    except _error as e:
        raise SocketError(Error_Other, str(e))
    if result:
        return result
    raise SocketError(Error_SocketClosed)


def SendUByte(sock: socket, i: int):
    _sendall(sock, pack(UByteFormat, i))


def RecvUByte(sock: socket) -> int:
    result = _recv(sock, UByteSize)
    return unpack(UByteFormat, result)[0]


def SendInt(sock: socket, i: int):
    _sendall(sock, pack(IntFormat, i))


def RecvInt(sock: socket) -> int:
    result = _recv(sock, IntSize)
    return unpack(IntFormat, result)[0]


def SendULong(sock: socket, i: int):
    _sendall(sock, pack(ULongFormat, i))


def RecvULong(sock: socket) -> int:
    result = _recv(sock, ULongSize)
    return unpack(ULongFormat, result)[0]


def _sendChunk(sock: socket, chunk: bytes):
    _sendall(sock, chunk)


def RecvChunk(sock: socket) -> bytes:
    return _recv(sock, ChunkSize)


def SendBytes(sock: socket, bts: bytes):
    size = len(bts)
    # Send size
    SendULong(sock, size)
    if size > 0:
        # Get number of chunks
        chunks = ceil(size / ChunkSize)
        # Send all chunks
        for i in range(chunks):
            this = bts[i * ChunkSize:(i + 1) * ChunkSize]
            _sendChunk(sock, this)


def RecvBytes(sock: socket) -> bytes:
    # Get number of bytes
    size = RecvULong(sock)
    result = b''
    if size > 0:
        # Find chunk number
        chunks = ceil(size / ChunkSize)
        # Get all chunk except last
        for i in range(chunks - 1):
            result += RecvChunk(sock)
        # Last chunk will have different size, calculate it
        result += _recv(sock, size - (chunks - 1) * ChunkSize)
    return result


def SendStr(sock: socket, s: str):
    return SendBytes(sock, s.encode())


def RecvStr(sock: socket) -> str:
    return RecvBytes(sock).decode()


def print_progress(percent: float):
    percent = floor(percent * 100.)
    out = '\rProgress - %d%% [' % percent + '#' * percent + '.' * (100 - percent) + ']'
    print(out, end='')


def SendBytesProgress(sock: socket, bts: bytes):
    size = len(bts)
    # Send size
    SendULong(sock, size)
    if size > 0:
        print_progress(0.)
        sent = 0
        # Get number of chunks
        chunks = ceil(size / ChunkSize)
        # Send all chunks
        for i in range(chunks):
            this = bts[i * ChunkSize:(i + 1) * ChunkSize]
            _sendChunk(sock, this)
            sent += len(this)
            print_progress(sent / size)
        print()  # new line after line with '\r'


def RecvBytesProgress(sock: socket) -> bytes:
    # Get number of bytes
    size = RecvULong(sock)
    result = b''
    if size > 0:
        print_progress(0.)
        # Get number of chunks
        chunks = ceil(size / ChunkSize)
        # Get all chunk except last
        for i in range(chunks - 1):
            result += RecvChunk(sock)
            print_progress(len(result) / size)
        # Last chunk will have different size, calculate it
        result += _recv(sock, size - (chunks - 1) * ChunkSize)
        print_progress(len(result) / size)
        print()  # new line after line with '\r'
    return result
