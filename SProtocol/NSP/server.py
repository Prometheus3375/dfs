import functools

from Common import Logger as _loggerclass
from Common.Constants import StorageServerPort
from Common.Socket import connection
from NServer.Storage import GetStorage
from SProtocol.common import *
from .common import *

Logger = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def LogResponse(sock: socket, log: str) -> bool:
    re = RecvResponse(sock)
    if re == SUCCESS:
        Logger.add(log + ' - success')
        return True
    Logger.add(log + ' - fail -> ' + re)
    return False


def _cmd(cmd: CommandType):
    def __cmd(func):
        @functools.wraps(func)
        @connection(port=StorageServerPort)
        def wrapper(sock: socket, *args):
            SendWMI(sock, NameServer)
            SendCommand(sock, cmd)
            log = 'Ordering command \'%s\' to storage %s' % (Commands[cmd], sock.getpeername()[0])
            Logger.add(log)
            return func(sock, log, *args)

        return wrapper

    return __cmd


@_cmd(Cmd_Locate)
def locate(sock: socket, log: str) -> str:
    pubip = RecvStr(sock)
    Logger.add(log + ' - success')
    return pubip


@_cmd(Cmd_MKFile)
def mkfile(sock: socket, log: str, path: str) -> bool:
    SendStr(sock, path)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        if path in fs:
            fs.remove(path)
        fs.add(path, True)
        return True
    return False


@_cmd(Cmd_Remove)
def remove(sock: socket, log: str, path: str):
    SendStr(sock, path)
    LogResponse(sock, log)
    ip = sock.getpeername()[0]
    GetStorage(ip).remove(path)
