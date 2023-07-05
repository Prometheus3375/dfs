import functools
import os.path as ospath
from math import ceil

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
        # Receive all bytes
        bts = RecvBytes(sock)
        # Get number of chunks
        chunks = ceil(len(bts) / FileChunkSize)
        for i in range(chunks):
            # Write chunk
            fpath = ospath.join(validpath, str(i))
            with open(fpath, 'wb') as f:
                f.write(bts[i * FileChunkSize: (i + 1) * FileChunkSize])
        # Finish file replication
        Logger.add(log + ' - success')
        SendSignal(sock)
    Logger.add(mainlog + ' - success')
