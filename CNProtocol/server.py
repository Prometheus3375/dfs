from CNProtocol.common import *
from NServer.FileSystems import Actual, Pending
from NameServer import Logger

_cmd2func = {}
Results = EnumCode()
ResultType = int
Result_Fail = Results('fail')
Result_Success = Results('success')
Result_Denied = Results('denied')

Mes_UpdateLocal = ', use \'update\' command to update local replica'
Mes_Manipulated = f'Other user is manipulating \'%s\', wait several minutes'


def _reg(id: RCType):
    def register(func):
        if id in _cmd2func:
            raise ValueError('%d is set to %s' % (id, _cmd2func[id].__name__))
        _cmd2func[id] = func
        return func

    return register


def ServeClient(sock: socket):
    cmd = RecvCommand(sock)
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
    # Remove node on pending
    Pending.remove(path)
    # TODO: wait until all downloads with this file will be ended
    # TODO: gather all storage servers with path and delete on them
    # All OK, remove on actual
    Actual.remove(path)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has removed \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    return Result_Success


def _is_dir(sock: socket, path: str) -> bool:
    if Actual.isDir(path):
        SendResponse(sock, '\'%s\' is a directory on remote' % path + Mes_UpdateLocal)
        return True
    return False


@_reg(Command_Rename)
def rename(sock: socket) -> ResultType:
    path = RecvStr(sock)
    name = RecvStr(sock)
    t = (path, name)
    Logger.addHost(*sock.getpeername(), 'attempts to rename \'%s\' to \'%s\'' % t)
    # Check if can be renamed
    if Actual.cantBeRenamed(path, name):
        SendResponse(sock, '\'%s\' cannot be renamed to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
    if Pending.cantBeRenamed(path, name):
        SendResponse(sock, Mes_Manipulated % path)
        return Result_Denied
    # Check if path is file
    if _is_dir(sock, path):
        return Result_Denied
    # Can be renamed
    # Rename node on pending
    Pending.rename(path, name)
    # TODO: wait until all downloads with this file will be ended
    # TODO: gather all storage servers with path and rename on them
    # All OK, rename on actual
    Actual.rename(path, name)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has renamed \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return Result_Success


@_reg(Command_Move)
def move(sock: socket) -> ResultType:
    what = RecvStr(sock)
    to = RecvStr(sock)
    t = (what, to)
    Logger.addHost(*sock.getpeername(), 'attempts to move \'%s\' to \'%s\'' % t)
    # Check if can be moved
    if Actual.cantBeMoved(what, to):
        SendResponse(sock, '\'%s\' cannot be moved to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
    if Pending.cantBeMoved(what, to):
        SendResponse(sock, Mes_Manipulated % what)
        return Result_Denied
    # Check if file
    if _is_dir(sock, what):
        return Result_Denied
    # Can be moved
    # Move node on pending
    Pending.move(what, to)
    # TODO: wait until all downloads with this file will be ended
    # TODO: gather all storage servers with path and move on them
    # All OK, move on actual
    Actual.move(what, to)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has moved \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return Result_Success


@_reg(Command_Copy)
def copy(sock: socket) -> ResultType:
    what = RecvStr(sock)
    to = RecvStr(sock)
    t = (what, to)
    Logger.addHost(*sock.getpeername(), 'attempts to copy \'%s\' to \'%s\'' % t)
    # Check if can be copied
    if Actual.cantBeCopied(what, to):
        SendResponse(sock, '\'%s\' cannot be copied to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
    if Pending.cantBeCopied(what, to):
        SendResponse(sock, Mes_Manipulated % what)
        return Result_Denied
    # Check if file
    if _is_dir(sock, what):
        return Result_Denied
    # Can be copied
    # Copy node on pending
    Pending.copy(what, to)
    # TODO: gather all storage servers with path and copy on them
    # All OK, copy on actual
    Actual.copy(what, to)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has copied \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return Result_Success
