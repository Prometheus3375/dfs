import SProtocol.NSP.server as NSP
from CNProtocol.common import *
from Common.Constants import ReplicationFactor
from Common.JobEx import SendJob
from Common.Logger import Logger as _loggerclass
from Common.Socket import SocketError, SendULong
from Common.VFS import VFSException
from NServer import Jobs
from NServer.FileSystems import Actual
from NServer.Storage import GetAliveServers, GetASWithPath, GetStorage, FlushStorages

# region Common
Logger: _loggerclass = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


_cmd2func = {}
Results = EnumCode()
ResultType = int
Result_Fail = Results('fail')
Result_Success = Results('success')
Result_Denied = Results('denied')

Mes_UpdateLocal = ', use \'update\' command to update local replica'


def _reg(id: RCType):
    def register(func):
        if id in _cmd2func:
            raise ValueError('%d is set to %s' % (id, _cmd2func[id].__name__))
        _cmd2func[id] = func
        return func

    return register


def CallNSP(ip: str, func, *args):
    try:
        return func(ip, *args)
    except NSP.NSPException as e:
        Logger.addError('A protocol error occurred during connecting to storage %s' % ip, e)
    except SocketError as e:
        Logger.addError('A socket error occurred during connecting to storage %s' % ip, e)
    except VFSException as e:
        Logger.addError('A VFS error occurred during connecting to storage %s' % ip, e)
    except Exception as e:
        Logger.addError('An unknown error occurred during connecting to storage %s' % ip, e)


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


# endregion
@_reg(Command_Update)
def update(sock: socket) -> ResultType:
    pts = Actual.walkWithTypes()
    SendStr(sock, '\n'.join(pts))
    return Result_Success


# region Make node
def _cant_add_node(sock: socket, path: str) -> bool:
    Logger.addHost(*sock.getpeername(), 'attempts to add \'%s\'' % path)
    if Actual.cantBeAdded(path):
        SendResponse(sock, '\'%s\' already exists on remote' % path)
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
    # Add file on ReplicationFactor servers
    count = 0
    for ip in GetAliveServers():
        if CallNSP(ip, NSP.mkfile, path):
            count += 1
            if count == ReplicationFactor: break
    # No server added - no update on actual
    if count == 0:
        SendResponse(sock, '\'%s\' cannot be created on remote' % path)
        return Result_Denied
    # Response
    Actual.add(path, False)
    return _node_added(sock, path)


@_reg(Command_MKDir)
def mkdir(sock: socket) -> ResultType:
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    Actual.add(path, True)
    return _node_added(sock, path)


# endregion
@_reg(Command_Remove)
def remove(sock: socket) -> ResultType:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to remove \'%s\'' % path)
    # Check if path can be deleted
    if Actual.cantBeRemoved(path):
        SendResponse(sock, '\'%s\' was already removed on remote' % path)
        return Result_Denied
    # Path can be deleted
    for ip in GetASWithPath(path):
        CallNSP(ip, NSP.remove, path)
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
    # Check if path is file
    if _is_dir(sock, path):
        return Result_Denied
    # Can be renamed
    count = 0
    for ip in GetASWithPath(path):
        if CallNSP(ip, NSP.rename, path, name):
            count += 1
    # No server renamed - no rename on actual
    if count == 0:
        SendResponse(sock, '\'%s\' cannot be renamed to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
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
    # Check if file
    if _is_dir(sock, what):
        return Result_Denied
    # Can be moved
    count = 0
    for ip in GetASWithPath(what):
        if CallNSP(ip, NSP.move, what, to):
            count += 1
    # No server moved - no move on actual
    if count == 0:
        SendResponse(sock, '\'%s\' cannot be moved to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
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
    # Check if file
    if _is_dir(sock, what):
        return Result_Denied
    # Can be copied
    count = 0
    for ip in GetASWithPath(what):
        if CallNSP(ip, NSP.copy, what, to):
            count += 1
    # No server copied - no copy on actual
    if count == 0:
        SendResponse(sock, '\'%s\' cannot be copied to \'%s\' on remote' % t + Mes_UpdateLocal)
        return Result_Denied
    # All OK, copy on actual
    Actual.copy(what, to)
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has copied \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return Result_Success


@_reg(Command_Flush)
def flush(sock: socket) -> ResultType:
    Logger.addHost(*sock.getpeername(), 'attempts to flush storage')
    space = 0
    for ip in GetAliveServers():
        rcvd = CallNSP(ip, NSP.flush)
        if rcvd: space += rcvd
    space //= ReplicationFactor
    # All OK, flush actual
    Actual.flush()
    FlushStorages()
    # Add log and response
    Logger.addHost(*sock.getpeername(), 'has flushed storage')
    SendULong(sock, space)
    return Result_Success


@_reg(Command_Info)
def info(sock: socket) -> ResultType:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to get stats of \'%s\'' % path)
    if path not in Actual:
        SendResponse(sock, '\'%s\' does not exist on remote' % path + Mes_UpdateLocal)
        return Result_Denied
    # Check if file
    if _is_dir(sock, path):
        return Result_Denied
    # Exists
    stats = None
    for ip in GetASWithPath(path):
        stats = CallNSP(ip, NSP.info, path)
        if stats: break
    if stats is None:
        SendResponse(sock, '\'%s\' does not have stats' % path)
        return Result_Denied
    # All OK, response
    Logger.addHost(*sock.getpeername(), 'has got stats of \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    SendStr(sock, stats)
    return Result_Success


@_reg(Command_Upload)
def upload(sock: socket) -> ResultType:
    path = RecvStr(sock)
    if _cant_add_node(sock, path):
        return Result_Denied
    # Create Job
    job = Jobs.new(sock)
    # Select server
    loader = ''
    for ip in GetAliveServers():
        if CallNSP(ip, NSP.upload, job, path):
            loader = ip
            break
    if not loader:
        SendResponse(sock, '\'%s\' cannot be uploaded' % path)
        Jobs.complete(job)
        return Result_Denied
    # Response client
    loaderfs = GetStorage(loader)
    SendResponse(sock, SUCCESS)
    SendJob(sock, job)
    SendStr(sock, loaderfs.pubip)
    # Get answer from client
    re = RecvResponse(sock)
    # Complete job
    Jobs.complete(job)
    # Check answer
    if re != SUCCESS:
        return Result_Fail
    # All OK, add on actual
    Actual.add(path, False)
    # Add to storage
    if path in loaderfs:
        loaderfs.remove(path)
    loaderfs.add(path, False)
    # Log
    Logger.addHost(*sock.getpeername(), 'has added \'%s\'' % path)
    # Init replication
    NSP.ReplicateFromOne(loader, [path])
    return Result_Success


@_reg(Command_Download)
def download(sock: socket) -> ResultType:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to download \'%s\'' % path)
    # Check if exists
    if path not in Actual:
        SendResponse(sock, '\'%s\' does not exist on remote' % path + Mes_UpdateLocal)
        return Result_Denied
    # Check if file
    if _is_dir(sock, path):
        return Result_Denied
    # Can be downloaded
    # Create Job
    job = Jobs.new(sock)
    # Select server
    loader = ''
    for ip in GetASWithPath(path):
        if CallNSP(ip, NSP.download, job, path):
            loader = ip
            break
    # No server has file - cannot be downloaded
    if not loader:
        SendResponse(sock, '\'%s\' cannot be downloaded' % path + Mes_UpdateLocal)
        Jobs.complete(job)
        return Result_Denied
    # Response client
    SendResponse(sock, SUCCESS)
    SendJob(sock, job)
    SendStr(sock, GetStorage(loader).pubip)
    # Get answer from client
    re = RecvResponse(sock)
    # Complete job
    Jobs.complete(job)
    # Check answer
    if re != SUCCESS:
        return Result_Fail
    # Log
    Logger.addHost(*sock.getpeername(), 'has downloaded \'%s\'' % path)
    return Result_Success
