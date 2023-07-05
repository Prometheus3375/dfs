from Common.Socket import *
from NServer import Logger
from NServer.FileSystems import Actual, Pending
from .common import *

_cmd2func = {}
Results = EnumCode()
Result_Fail = Results('fail')
Result_Success = Results('success')
Result_Denied = Results('denied')


def _reg(id: int):
    def register(func):
        if id in _cmd2func:
            raise ValueError('%d is set to %s' % (id, _cmd2func[id].__name__))
        _cmd2func[id] = func
        return func

    return register


def RecvCommand(sock: socket):
    cmd = RecvInt(sock)
    if cmd in _cmd2func:
        # noinspection PyStringFormat
        log = '%s:%d issued command \'%s\'' % (*sock.getpeername(), RemoteCommands[cmd])
        Logger.add(log)
        res = Result_Fail
        try:
            res = _cmd2func[cmd](sock)
        finally:
            Logger.add(log + ' - ' + Results[res])
    else:
        raise CNPException('Invalid command passed from client %s:%d' % sock.getpeername())


@_reg(Command_Update)
def update(sock: socket) -> int:
    pts = Actual.walkWithTypes()
    SendStr(sock, '\n'.join(pts))
    return Result_Success


def _cant_add_node(sock: socket, path: str) -> bool:
    # noinspection PyStringFormat
    Logger.addHost(*sock.getpeername(), 'attempts to add \'%s\'' % path)
    if Actual.cantBeAdded(path):
        SendStr(sock, '\'%s\' already exists on remote. Use \'update\' command to update local replica' % path)
        return True
    if Pending.cantBeAdded(path):
        SendStr(sock, '\'%s\' is adding by other user, wait several minutes' % path)
        return True
    return False


def _node_added(sock: socket, path: str) -> int:
    # noinspection PyStringFormat
    Logger.addHost(*sock.getpeername(), 'has added \'%s\'' % path)
    SendStr(sock, SUCCESS)
    return Result_Success


@_reg(Command_MKFile)
def mkfile(sock: socket) -> int:
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    node = Pending.add(path, False)
    # TODO: create job
    # TODO: select 2 servers and create a file on them
    # TODO: if NSP error occur, select another server
    Actual.add(path, False)
    return _node_added(sock, path)


@_reg(Command_MKDir)
def mkfile(sock: socket):
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    Pending.add(path, True)
    Actual.add(path, True)
    return _node_added(sock, path)
