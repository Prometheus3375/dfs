import os.path as ospath
from math import ceil

import SServer.FSFuncs as FS
import SServer.Jobs as Jobs
from Common.JobEx import RecvJob
from Common.Logger import Logger as _loggerclass
from Common.Socket import RecvBytes, SendULong, SendBytes
from SProtocol.CSP.common import *

Logger: _loggerclass = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


def ServeClient(sock: socket):
    job = RecvJob(sock)
    j = Jobs.StartJob(sock, job)
    if j:
        path = j.paths[0]
        if j.typ == Jobs.JT_Upload:
            upload(sock, path)
        elif j.typ == Jobs.JT_Download:
            download(sock, path)
        elif j.typ == Jobs.JT_Replicate:
            raise CSPException('Replication job passed from client %s:%d' % sock.getpeername())
        else:
            raise CSPException('Unknown job passed from client %s:%d' % sock.getpeername())
    else:
        raise CSPException('Invalid job passed from client %s:%d' % sock.getpeername())


def upload(sock: socket, path: str):
    Logger.addHost(*sock.getpeername(), 'attempts to upload a file to \'%s\'' % path)
    validpath = FS.CreateFile(path)
    bts = RecvBytes(sock)
    chunks = ceil(len(bts) / FileChunkSize)
    for i in range(chunks):
        fpath = ospath.join(validpath, str(i))
        with open(fpath, 'wb') as f:
            f.write(bts[i * FileChunkSize: (i + 1) * FileChunkSize])
    Logger.addHost(*sock.getpeername(), 'has uploaded file \'%s\'' % path)
    SendResponse(sock, SUCCESS)


def download(sock: socket, path: str):
    Logger.addHost(*sock.getpeername(), 'attempts to download \'%s\'' % path)
    # Check if exists
    if not FS.Exists(path):
        SendResponse(sock, 'No such file on storage server')
        return
    # Get chunks number and valid path
    chunks = ceil(FS.GetSize(path) / FileChunkSize)
    validpath = FS.GetValidPath(path)
    # Send file
    SendULong(sock, chunks)
    RecvSignal(sock)
    for i in range(chunks):
        fpath = ospath.join(validpath, str(i))
        with open(fpath, 'rb') as f:
            SendBytes(sock, f.read())
