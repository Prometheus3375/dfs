from Common.Socket import socket, RecvStr, SendStr
from SProtocol.common import SPException

FileChunkSize = 1024 * 1024  # in bytes

ResponseType = str
SUCCESS = ''


class SSPException(SPException):
    pass


def SendResponse(sock: socket, re: ResponseType):
    SendStr(sock, re)


def RecvResponse(sock: socket) -> ResponseType:
    return RecvStr(sock)
