import functools

from CNProtocol.common import *
from Common.Socket import connection, RecvULong


def _cmd(cmd: RCType):
    def __cmd(func):
        @functools.wraps(func)
        @connection()
        def wrapper(sock: socket, *args):
            SendCommand(sock, cmd)
            return func(sock, *args)

        return wrapper

    return __cmd


@_cmd(Command_Update)
def update(sock: socket):
    paths_types = RecvStr(sock).strip()
    return paths_types.split(Update_LineSeparator)


@connection()
def create(sock: socket, path: str, isDir: bool) -> ResponseType:
    SendCommand(sock, Command_MKDir if isDir else Command_MKFile)
    SendStr(sock, path)
    return RecvResponse(sock)


@_cmd(Command_Remove)
def remove(sock: socket, path: str) -> ResponseType:
    SendStr(sock, path)
    return RecvResponse(sock)


@_cmd(Command_Rename)
def rename(sock: socket, path: str, name: str) -> ResponseType:
    SendStr(sock, path)
    SendStr(sock, name)
    return RecvResponse(sock)


@_cmd(Command_Move)
def move(sock: socket, what: str, to: str) -> ResponseType:
    SendStr(sock, what)
    SendStr(sock, to)
    return RecvResponse(sock)


@_cmd(Command_Copy)
def copy(sock: socket, what: str, to: str) -> ResponseType:
    SendStr(sock, what)
    SendStr(sock, to)
    return RecvResponse(sock)


@_cmd(Command_Flush)
def flush(sock: socket) -> int:
    return RecvULong(sock)


@_cmd(Command_Info)
def info(sock: socket, what: str):
    SendStr(sock, what)
    re = RecvResponse(sock)
    if re == SUCCESS:
        return RecvStr(sock).strip().split(InfoSeparator)
    return re


@_cmd(Command_Upload)
def upload(sock: socket, real: str, virt: str) -> ResponseType:
    SendStr(sock, virt)
    # TODO
    return RecvResponse(sock)


@_cmd(Command_Flush)
def download(sock: socket, virt: str, real: str) -> ResponseType:
    SendStr(sock, virt)
    # TODO
    return RecvResponse(sock)
