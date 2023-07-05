import functools
from threading import Thread

from Common import Logger as _loggerclass
from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Socket import connection, RecvULong, SocketError
from Common.VFS import Join, VFSException
from NServer import Jobs
from NServer.Storage import GetStorage, GetASNoPath, GetASWithPath
from SProtocol.NSP.common import *
from SProtocol.common import *

Logger = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def LogResponse(sock: socket, log: str) -> bool:
    re = RecvResponse(sock)
    if re == SUCCESS:
        Logger.add(log + ' - success')
        return True
    Logger.add(log + ' - fail' + (' -> ' + re if re else ''))
    return False


def _cmd(cmd: CommandType):
    def __cmd(func):
        @functools.wraps(func)
        @connection(port=StorageServerPort)
        def wrapper(sock: socket, *args):
            SendWMI(sock, NameServer)
            SendCommand(sock, cmd)
            log = 'Ordering command \'%s\' to storage %s' % (Commands[cmd], sock.getpeername()[0])
            Logger.add(log)
            return func(sock, log, *args)

        return wrapper

    return __cmd


@_cmd(Cmd_Locate)
def locate(sock: socket, log: str) -> tuple:
    pubip = RecvStr(sock)
    space = RecvULong(sock)
    Logger.add(log + ' - success')
    return pubip, space


@_cmd(Cmd_MKFile)
def mkfile(sock: socket, log: str, path: str) -> bool:
    SendStr(sock, path)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        if path in fs:
            fs.remove(path)
        fs.add(path, True)
        return True
    return False


@_cmd(Cmd_Remove)
def remove(sock: socket, log: str, path: str):
    SendStr(sock, path)
    LogResponse(sock, log)
    ip = sock.getpeername()[0]
    GetStorage(ip).remove(path)


@_cmd(Cmd_Rename)
def rename(sock: socket, log: str, path: str, name: str) -> bool:
    SendStr(sock, path)
    SendStr(sock, name)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        names = fs.parsePath(path)[1]
        names[-1] = name
        newpath = Join(*names)
        if newpath in fs:
            fs.remove(newpath)
        fs.rename(path, name)
        return True
    return False


@_cmd(Cmd_Move)
def move(sock: socket, log: str, what: str, to: str) -> bool:
    SendStr(sock, what)
    SendStr(sock, to)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        name = fs.nodeAt(what).name
        newpath = Join(to, name)
        if newpath in fs:
            fs.remove(newpath)
        fs.move(what, to)
        return True
    return False


@_cmd(Cmd_Copy)
def copy(sock: socket, log: str, what: str, to: str) -> bool:
    SendStr(sock, what)
    SendStr(sock, to)
    if LogResponse(sock, log):
        ip = sock.getpeername()[0]
        fs = GetStorage(ip)
        name = fs.nodeAt(what).name
        newpath = Join(to, name)
        if newpath in fs:
            fs.remove(newpath)
        fs.copy(what, to)
        return True
    return False


@_cmd(Cmd_Flush)
def flush(sock: socket, log: str) -> int:
    res = RecvULong(sock)
    Logger.add(log + ' - success')
    return res


@_cmd(Cmd_Info)
def info(sock: socket, log: str, path: str) -> str:
    SendStr(sock, path)
    res = RecvStr(sock)
    Logger.add(log + ' - success')
    return res


@_cmd(Cmd_Upload)
def upload(sock: socket, log: str, job: int, path: str) -> bool:
    SendJob(sock, job)
    SendStr(sock, path)
    return LogResponse(sock, log)


@_cmd(Cmd_Download)
def download(sock: socket, log: str, job: int, path: str) -> bool:
    SendJob(sock, job)
    SendStr(sock, path)
    return LogResponse(sock, log)


@_cmd(Cmd_PrepareReplicate)
def prepare_replicate(sock: socket, log: str, job: int, paths: list) -> bool:
    send = PathSeparator.join(paths)
    SendJob(sock, job)
    SendStr(sock, send)
    return LogResponse(sock, log)


@_cmd(Cmd_DoReplicate)
def do_replicate(sock: socket, log: str, loader_ip: str, job: int, paths: list) -> bool:
    if prepare_replicate(loader_ip, job, paths):
        SendJob(sock, job)
        SendStr(sock, loader_ip)
        return LogResponse(sock, log)
    Logger.add(log + ' - fail')
    return False


def _replicate_from_one(loader: str, paths: list):
    servers = {}
    # Get dict of servers to replicate
    for path in paths:
        ips = GetASNoPath(path)
        for ip in ips:
            if ip in servers:
                servers[ip].append(path)
            else:
                servers[ip] = [path]
    # Try to replicate
    for ip, pts in servers.items():
        # Remove paths already replicated
        pts = [p for p in pts if p in paths]
        if not pts: continue
        job = Jobs.new()
        try:
            if do_replicate(loader, job, pts):
                # Success, update storage data
                fs = GetStorage(ip)
                for p in pts:
                    if p in fs:
                        fs.remove(p)
                    fs.add(p, False)
                # Remove replicated paths
                paths = [path for path in paths if path not in pts]
                # Break if all replicated
                if not paths: break
        except NSPException as e:
            Logger.add('A protocol error occurred during connecting to storage %s: ' % ip + str(e))
        except SocketError as e:
            Logger.add('A socket error occurred during connecting to storage %s: ' % ip + str(e))
        except VFSException as e:
            Logger.add('A VFS error occurred during connecting to storage %s: ' % ip + str(e))
        except Exception as e:
            Logger.add('An unknown error occurred during connecting to storage %s: ' % ip + str(e))
        Jobs.complete(job)
    return paths


def ReplicateFromOne(loader: str, paths: list):
    if not (loader and paths): return
    Thread(daemon=True, target=_replicate_from_one, args=(loader, paths)).start()


def _replicate(paths: list):
    servers = {}
    # Get dict of servers where that paths exists
    for path in paths:
        ips = GetASWithPath(path)
        for ip in ips:
            if ip in servers:
                servers[ip].append(path)
            else:
                servers[ip] = [path]
    # Replicate until all replicated
    for ip, pts in servers.items():
        # Remove paths already replicated
        pts = [p for p in pts if p in paths]
        # Continue if no paths
        if not pts: continue
        # Replicate from current
        remaining = _replicate_from_one(ip, pts)
        # Remove replicated paths
        paths = [path for path in paths if (path not in pts) or (path in remaining)]
        # Break if all replicated
        if not paths: break


def Replicate(paths: list):
    if not paths: return
    Thread(daemon=True, target=_replicate, args=(paths,)).start()
