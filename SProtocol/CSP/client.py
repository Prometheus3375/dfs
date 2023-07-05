import functools
import os
from math import ceil

from Common.Socket import connection, SendBytes, RecvBytes, SendULong, RecvULong
from SProtocol.CSP.common import *
from SProtocol.common import SendWMI, Client


def _cmd(func):
    @functools.wraps(func)
    @connection()
    def wrapper(sock: socket, job: int, *args):
        SendWMI(sock, Client)
        SendInt(sock, job)
        return func(sock, *args)

    return wrapper


@_cmd
def upload(sock: socket, path: str):
    chunks = ceil(os.path.getsize(path) / FileChunkSize)
    SendULong(sock, chunks)
    with open(path, 'rb') as f:
        bts = f.read(FileChunkSize)
        while bts:
            SendBytes(sock, bts)
            bts = f.read(FileChunkSize)


@_cmd
def download(sock: socket, path: str):
    chunks = RecvULong(sock)
    with open(path, 'wb') as f:
        for i in range(chunks):
            f.write(RecvBytes(sock))
