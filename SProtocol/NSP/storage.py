import os.path as ospath

import SServer.FSFuncs as FS
import SServer.Jobs as Jobs
from Common import Logger as _loggerclass
from Common.JobEx import RecvJob
from Common.Socket import SendULong
from SProtocol.NSP.common import *

Logger = ...
PublicIP = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def SetPublicIP(ip: str):
    global PublicIP
    PublicIP = ip


_cmd2func = {}


def _reg(id: CommandType):
    def register(func):
        if id in _cmd2func:
            raise ValueError('%d is set to %s' % (id, _cmd2func[id].__name__))
        _cmd2func[id] = func
        return func

    return register


def ServeNameServer(sock: socket):
    cmd = RecvCommand(sock)
    if cmd in _cmd2func:
        # noinspection PyStringFormat
        log = '%s:%d issued command \'%s\'' % (*sock.getpeername(), Commands[cmd])
        Logger.add(log)
        fail = True
        try:
            fail = _cmd2func[cmd](sock)
        finally:
            Logger.add(log + ' - ' + ('fail' if fail else 'success'))
    else:
        raise NSPException('Invalid command passed from nameserver %s:%d' % sock.getpeername())


@_reg(Cmd_Locate)
def locate(sock: socket) -> bool:
    SendStr(sock, PublicIP)
    SendULong(sock, FS.GetFreeSpace())
    return False


@_reg(Cmd_MKFile)
def mkfile(sock: socket) -> bool:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to create an empty file \'%s\'' % path)
    fpath = ospath.join(FS.CreateFile(path), '0')  # zero chunk
    with open(fpath, 'wb'): pass
    Logger.addHost(*sock.getpeername(), 'has created \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    return False


@_reg(Cmd_Remove)
def remove(sock: socket) -> bool:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to remove \'%s\'' % path)
    FS.Remove(path)
    Logger.addHost(*sock.getpeername(), 'has removed \'%s\'' % path)
    SendResponse(sock, SUCCESS)
    return False


@_reg(Cmd_Rename)
def rename(sock: socket) -> bool:
    path = RecvStr(sock)
    name = RecvStr(sock)
    t = path, name
    Logger.addHost(*sock.getpeername(), 'attempts to rename \'%s\' to \'%s\'' % t)
    FS.Rename(path, name)
    Logger.addHost(*sock.getpeername(), 'has renamed \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return False


@_reg(Cmd_Move)
def move(sock: socket) -> bool:
    what = RecvStr(sock)
    to = RecvStr(sock)
    t = what, to
    Logger.addHost(*sock.getpeername(), 'attempts to move \'%s\' to \'%s\'' % t)
    FS.Move(what, to)
    Logger.addHost(*sock.getpeername(), 'has moved \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return False


@_reg(Cmd_Copy)
def copy(sock: socket) -> bool:
    what = RecvStr(sock)
    to = RecvStr(sock)
    t = what, to
    Logger.addHost(*sock.getpeername(), 'attempts to copy \'%s\' to \'%s\'' % t)
    FS.Copy(what, to)
    Logger.addHost(*sock.getpeername(), 'has copied \'%s\' to \'%s\'' % t)
    SendResponse(sock, SUCCESS)
    return False


@_reg(Cmd_Flush)
def flush(sock: socket) -> bool:
    Logger.addHost(*sock.getpeername(), 'attempts to flush file system')
    FS.Flush()
    space = FS.GetFreeSpace()
    Logger.addHost(*sock.getpeername(), 'has flushed file system')
    SendULong(sock, space)
    return False


@_reg(Cmd_Info)
def info(sock: socket) -> bool:
    path = RecvStr(sock)
    Logger.addHost(*sock.getpeername(), 'attempts to get stats of \'%s\'' % path)
    stats = FS.GetStats(path)
    stats = [str(st) for st in stats]
    stats = InfoSeparator.join(stats)
    Logger.addHost(*sock.getpeername(), 'has got stats of \'%s\'' % path)
    SendStr(sock, stats)
    return False


@_reg(Cmd_Upload)
def upload(sock: socket) -> bool:
    job = RecvJob(sock)
    path = RecvStr(sock)
    j = Jobs.AddUploadJob(job, path)
    SendResponse(sock, SUCCESS)
    if not j.wait(LoadTimeout):
        Jobs.CompleteJob(job)
        return True
    return False
