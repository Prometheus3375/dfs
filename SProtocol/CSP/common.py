from Common.Socket import socket, RecvStr, SendStr, SendUByte, RecvUByte
from SProtocol.common import SPException

FileChunkSize = 1024 * 1024  # in bytes

ResponseType = str
SUCCESS = ''


class CSPException(SPException):
    pass


def SendResponse(sock: socket, re: ResponseType):
    SendStr(sock, re)


def RecvResponse(sock: socket) -> ResponseType:
    return RecvStr(sock)


def SendSignal(sock: socket):
    SendUByte(sock, 0)


def RecvSignal(sock: socket) -> int:
    return RecvUByte(sock)
