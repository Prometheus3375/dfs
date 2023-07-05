import os.path as ospath

import SServer.FSFuncs as FS
import SServer.Jobs as Jobs
from Common import Logger as _loggerclass
from Common.JobEx import RecvJob
from Common.Socket import RecvULong, RecvBytes
from SProtocol.CSP.common import *

Logger = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def ServeClient(sock: socket):
    job = RecvJob(sock)
    j = Jobs.StartJob(sock, job)
    if j:
        if j.typ == Jobs.JT_Upload:
            upload(sock, j.path)
        elif j.typ == Jobs.JT_Download:
            download(sock, j.path)
        else:
            raise CSPException('Replication job passed from client %s:%d' % sock.getpeername())
    else:
        raise CSPException('Invalid job passed from client %s:%d' % sock.getpeername())


def upload(sock: socket, path: str):
    Logger.addHost(*sock.getpeername(), 'attempts to upload a file to %s' % path)
    validpath = FS.CreateFile(path)
    chunks = RecvULong(sock)
    for i in range(chunks):
        fpath = ospath.join(validpath, str(i))
        with open(fpath, 'wb') as f:
            f.write(RecvBytes(sock))
    Logger.addHost(*sock.getpeername(), 'has uploaded file %s' % path)
    SendResponse(sock, SUCCESS)


def download(sock: socket, path: str):
    pass
