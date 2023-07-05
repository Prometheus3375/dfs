from Common.Misc import EnumCode
from Common.Socket import socket, SendInt, RecvInt
from SProtocol.common import SPException

RemoteCommands = EnumCode()
RCType = int

Command_Upload = RemoteCommands('upload')
Command_Download = RemoteCommands('download')

FileChunkSize = 1024 * 1024  # in bytes


class CSPException(SPException):
    pass


def SendCommand(sock: socket, cmd: RCType):
    SendInt(sock, cmd)


def RecvCommand(sock: socket) -> RCType:
    return RecvInt(sock)
