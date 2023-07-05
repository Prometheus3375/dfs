from Common.Socket import *
from NServer.FSDriver import WalkActual
from .common import *

Command2Func = {}


def _reg(id: int):
    def _register(func):
        if id in Command2Func:
            raise ValueError('%d is set to %s' % (id, Command2Func[id].__name__))
        Command2Func[id] = func

    return _register


def RecvCommand(sock: socket):
    cmd = RecvInt(sock)
    if RemoteCommands.valid(cmd):
        Command2Func[cmd](sock)
    else:
        raise CNPError('Invalid command passed from client %s:%d' % sock.getpeername())


@_reg(Command_Update)
def update(sock: socket):
    pts = WalkActual()
    SendStr(sock, '\n'.join(pts))
