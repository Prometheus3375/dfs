import functools

from Common import Logger as _loggerclass
from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Socket import connection, RecvULong
from Common.VFS import Join
from NServer.Storage import GetStorage
from SProtocol.NSP.common import *
from SProtocol.common import *

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
def locate(sock: socket, log: str) -> tuple:
    pubip = RecvStr(sock)
    space = RecvULong(sock)
    Logger.add(log + ' - success')
    return pubip, space


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


@_cmd(Cmd_Rename)
def rename(sock: socket, log: str, path: str, name: str) -> bool:
    SendStr(sock, path)
    SendStr(sock, name)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        names = fs.parsePath(path)[1]
        names[-1] = name
        newpath = Join(*names)
        if newpath in fs:
            fs.remove(newpath)
        fs.rename(path, name)
        return True
    return False


@_cmd(Cmd_Move)
def move(sock: socket, log: str, what: str, to: str) -> bool:
    SendStr(sock, what)
    SendStr(sock, to)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        name = fs.nodeAt(what).name
        newpath = Join(to, name)
        if newpath in fs:
            fs.remove(newpath)
        fs.move(what, to)
        return True
    return False


@_cmd(Cmd_Copy)
def copy(sock: socket, log: str, what: str, to: str) -> bool:
    SendStr(sock, what)
    SendStr(sock, to)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        name = fs.nodeAt(what).name
        newpath = Join(to, name)
        if newpath in fs:
            fs.remove(newpath)
        fs.copy(what, to)
        return True
    return False


@_cmd(Cmd_Flush)
def flush(sock: socket, log: str) -> int:
    res = RecvULong(sock)
    Logger.add(log + ' - success')
    return res


@_cmd(Cmd_Info)
def info(sock: socket, log: str, path: str) -> str:
    SendStr(sock, path)
    res = RecvStr(sock)
    Logger.add(log + ' - success')
    return res


@_cmd(Cmd_Upload)
def upload(sock: socket, log: str, job: int, path: str) -> bool:
    SendJob(sock, job)
    SendStr(sock, path)
    return LogResponse(sock, log)


@_cmd(Cmd_Replicate)
def replicate(sock: socket, log: str, job: int, path: str) -> bool:
    SendJob(sock, job)
    SendStr(sock, path)
    return LogResponse(sock, log)
