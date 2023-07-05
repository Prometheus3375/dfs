import functools

from CNProtocol.common import *


def _cmd(cmd: RCType):
    def __cmd(func):
        @functools.wraps(func)
        @connect
        def wrapper(sock: socket, *args):
            SendCommand(sock, cmd)
            return func(sock, *args)

        return wrapper

    return __cmd


@_cmd(Command_Update)
def update(sock: socket):
    paths_types = RecvStr(sock).strip()
    return paths_types.split(Update_LineSeparator)


@connect
def create(sock: socket, path: str, isDir: bool) -> ResponseType:
    SendCommand(sock, Command_MKDir if isDir else Command_MKFile)
    SendStr(sock, path)
    return RecvResponse(sock)


@_cmd(Command_Remove)
def remove(sock: socket, path: str) -> ResponseType:
    SendStr(sock, path)
    return RecvResponse(sock)
