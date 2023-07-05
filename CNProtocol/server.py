from CNProtocol.common import *
from NServer.FileSystems import Actual, Pending
from NameServer import Logger

_cmd2func = {}
Results = EnumCode()
ResultType = int
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


def ServeClient(sock: socket):
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
def update(sock: socket) -> ResultType:
    pts = Actual.walkWithTypes()
    SendStr(sock, '\n'.join(pts))
    return Result_Success


def _cant_add_node(sock: socket, path: str) -> bool:
    Logger.addHost(*sock.getpeername(), 'attempts to add \'%s\'' % path)
    if Actual.cantBeAdded(path):
        SendResponse(sock, '\'%s\' already exists on remote' % path)
        return True
    if Pending.cantBeAdded(path):
        SendResponse(sock, '\'%s\' is being added by other user' % path)
        return True
    return False


def _node_added(sock: socket, path: str) -> ResultType:
    Logger.addHost(*sock.getpeername(), 'has added \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    return Result_Success


@_reg(Command_MKFile)
def mkfile(sock: socket) -> ResultType:
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    node = Pending.add(path, False)
    # TODO: create job
    # TODO: select 2 storage servers and create a file on them
    # TODO: if NSP error occur, select another server
    Actual.add(path, False)
    return _node_added(sock, path)


@_reg(Command_MKDir)
def mkfile(sock: socket) -> ResultType:
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    Pending.add(path, True)
    Actual.add(path, True)
    return _node_added(sock, path)


@_reg(Command_Remove)
def remove(sock: socket) -> ResultType:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to remove \'%s\'' % path)
    # Check if path can be deleted
    if Actual.cantBeRemoved(path):
        SendResponse(sock, '\'%s\' was already removed on remote' % path)
        return Result_Denied
    if Pending.cantBeRemoved(path):
        SendResponse(sock, '\'%s\' is being removed by other user' % path)
        return Result_Denied
    # Path can be deleted
    # Remove node at pending
    Pending.remove(path)
    # TODO: wait until all downloads with this file will be ended
    # TODO: gather all storage servers with path and delete on them
    # All OK, remove on actual
    Actual.remove(path)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has removed \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    return Result_Success


@_reg(Command_Rename)
def rename(sock: socket) -> ResultType:
    path = RecvStr(sock)
    name = RecvStr(sock)
    # Check if path exists
    if not Actual.exists(path):
        SendResponse(sock,
                     '\'%s\' has been removed on remote, use \'update\' command to update local replica' % path)
        return Result_Denied
    if not Pending.exists(path):
        SendResponse(sock, '\'%s\' is being removed by other user, wait several minutes' % path)
        return Result_Denied
    # Check if path is file
    if Actual.isDir(path):
        SendResponse(sock, '\'%s\' is a directory on remote, use \'update\' command to update local replica' % path)
        return Result_Denied
    # Check if can be renamed
    if Actual.cantBeRenamed(path, name):
        SendResponse(sock, 'Parent of \'%s\' contains \'%s\' on remote, use \'update\' command to update local replica'
                     % (path, name))
        return Result_Denied
    if Pending.cantBeRenamed(path, name):
        SendResponse(sock, '\'%s\' is being added by other user, wait several minutes' % path)
        return Result_Denied
    # Can be renamed
    # Rename node at pending
    Pending.rename(path, name)
    # TODO: wait until all downloads with this file will be ended
    # TODO: gather all storage servers with path and rename on them
    # All OK, rename on actual
    node = Actual.rename(path, name)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has renamed \'%s\' to \'%s\'' % (path, node.getPath()))
    SendResponse(sock, SUCCESS)
    return Result_Success
