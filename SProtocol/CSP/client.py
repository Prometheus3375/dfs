import functools
import os.path as ospath
from math import ceil, floor

from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Socket import connection, SendBytes, RecvBytes, SendULong, RecvULong
from SProtocol.CSP.common import *
from SProtocol.common import SendWMI, Client


def _cmd(func):
    @functools.wraps(func)
    @connection(port=StorageServerPort)
    def wrapper(sock: socket, job: int, *args):
        SendWMI(sock, Client)
        SendJob(sock, job)
        return func(sock, *args)

    return wrapper


def print_progress(percent: float):
    percent = floor(percent * 100.)
    out = '\rProgress - %3d%% [' % percent + '#' * percent + '.' * (100 - percent) + ']'
    print(out, end='')


@_cmd
def upload(sock: socket, path: str) -> bool:
    size = ospath.getsize(path)
    chunks = ceil(size / FileChunkSize)
    SendULong(sock, chunks)
    processed = 0
    print_progress(processed / size)
    with open(path, 'rb') as f:
        bts = f.read(FileChunkSize)
        while bts:
            SendBytes(sock, bts)
            processed += len(bts)
            print_progress(processed / size)
            bts = f.read(FileChunkSize)
    print()  # new line
    return RecvResponse(sock) == SUCCESS


@_cmd
def download(sock: socket, path: str):
    chunks = RecvULong(sock)
    with open(path, 'wb') as f:
        for i in range(chunks):
            f.write(RecvBytes(sock))
