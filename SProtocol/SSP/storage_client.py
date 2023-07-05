import functools
import os.path as ospath

import SServer.FSFuncs as FS
from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Logger import Logger as _loggerclass
from Common.Socket import connection, RecvBytes, RecvULong
from SProtocol.common import SendWMI, StorageServer
from .common import *

Logger: _loggerclass = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def _cmd(func):
    @functools.wraps(func)
    @connection(port=StorageServerPort)
    def wrapper(sock: socket, job: int, *args):
        SendWMI(sock, StorageServer)
        SendJob(sock, job)
        return func(sock, *args)

    return wrapper


@_cmd
def replicate(sock: socket):
    host = sock.getpeername()[0]
    paths = RecvULong(sock)
    mainlog = f'Starting to replicate {paths} file(s) from storage %s' % host
    Logger.add(mainlog)
    # Start replication
    for _ in range(paths):
        # Receive path
        path = RecvStr(sock)
        log = f'Starting to replicate \'{path}\' from storage %s' % host
        Logger.add(log)
        # Prepare path
        validpath = FS.CreateFile(path)
        # Receive chunk number
        chunks = RecvULong(sock)
        # Write chunks
        for i in range(chunks):
            fpath = ospath.join(validpath, str(i))
            with open(fpath, 'wb') as f:
                f.write(RecvBytes(sock))
        # Finish file replication
        Logger.add(log + ' - success')
    Logger.add(mainlog + ' - success')
