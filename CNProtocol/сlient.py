from Common.Socket import *
from .common import *


def _send_cmd(sock: socket, cmd: int):
    SendInt(sock, cmd)


def _cmd(cmd: int):
    def __cmd(func):
        @functools.wraps(func)
        @connect
        def wrapper(sock: socket, *args):
            _send_cmd(sock, cmd)
            return func(sock, *args)

        return wrapper

    return __cmd


@_cmd(Command_Update)
def update(sock: socket):
    paths_types = RecvStr(sock).strip()
    return paths_types.split(Update_LineSeparator)


@connect
def create(sock: socket, path: str, isDir: bool):
    _send_cmd(sock, Command_MKDir if isDir else Command_MKFile)
    SendStr(sock, path)
    ans = RecvStr(sock)
    if ans != SUCCESS:
        raise CNPException(ans)
