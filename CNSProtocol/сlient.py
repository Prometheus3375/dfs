from Common.Socket import *
from . import *


def _sendCommand(sock: socket, cmd: int):
    SendInt(sock, cmd)


@connect
def update(sock: socket):
    _sendCommand(sock, Command_Update)
    paths_types = RecvStr(sock).strip()
    return paths_types.split(Update_PTSep)
