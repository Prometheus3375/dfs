import os.path as ospath
from math import ceil

import SServer.FSFuncs as FS
import SServer.Jobs as Jobs
from Common.JobEx import RecvJob
from Common.Logger import Logger as _loggerclass
from Common.Socket import SendULong, SendBytes
from .common import *

Logger: _loggerclass = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def ServeStorage(sock: socket):
    job = RecvJob(sock)
    j = Jobs.StartJob(sock, job)
    if j:
        paths = j.paths
        if j.typ == Jobs.JT_Upload:
            raise SSPException('Upload job passed from storage %s' % sock.getpeername()[0])
        elif j.typ == Jobs.JT_Download:
            raise SSPException('Download job passed from storage %s' % sock.getpeername()[0])
        elif j.typ == Jobs.JT_Replicate:
            replicate(sock, paths)
        else:
            raise SSPException('Unknown job passed from client %s:%d' % sock.getpeername())
    else:
        raise SSPException('Invalid job passed from client %s:%d' % sock.getpeername())


def replicate(sock: socket, paths: list):
    # Send paths number
    n = len(paths)
    Logger.addHost(*sock.getpeername(), 'attempts to replicate %d file(s) ' % n)
    SendULong(sock, n)
    for path in paths:
        Logger.addHost(*sock.getpeername(), 'attempts to replicate file \'%s\'' % path)
        # Send path
        RecvSignal(sock)
        SendStr(sock, path)
        # Get chunks number and valid path
        chunks = ceil(FS.GetSize(path) / FileChunkSize)
        validpath = FS.GetValidPath(path)
        # Send chunks
        RecvSignal(sock)
        SendULong(sock, chunks)
        # Send file chunk by chunk
        for i in range(chunks):
            fpath = ospath.join(validpath, str(i))
            with open(fpath, 'rb') as f:
                RecvSignal(sock)
                SendBytes(sock, f.read())
        Logger.addHost(*sock.getpeername(), 'has replicated file \'%s\'' % path)
    Logger.addHost(*sock.getpeername(), 'has replicated %d file(s) ' % n)
