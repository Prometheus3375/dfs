import SServer.FSFuncs as FS
from Common import Logger as _loggerclass
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
            _cmd2func[cmd](sock)
            fail = False
        finally:
            Logger.add(log + ' - ' + ('fail' if fail else 'success'))
    else:
        raise NSPException('Invalid command passed from nameserver %s:%d' % sock.getpeername())


@_reg(Cmd_Locate)
def locate(sock: socket):
    SendStr(sock, PublicIP)


@_reg(Cmd_MKFile)
def mkfile(sock: socket):
    path = RecvStr(sock)
    path = FS.CreateFile(path) + '0'  # zero chunk
    with open(path, 'wb'): pass
    SendResponse(sock, SUCCESS)


@_reg(Cmd_Remove)
def remove(sock: socket):
    path = RecvStr(sock)
    FS.Remove(path)
    SendResponse(sock, SUCCESS)


@_reg(Cmd_Rename)
def rename(sock: socket):
    path = RecvStr(sock)
    name = RecvStr(sock)
    FS.Rename(path, name)
    SendResponse(sock, SUCCESS)
