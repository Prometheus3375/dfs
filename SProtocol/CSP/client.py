import functools
from math import floor

from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Socket import connection, SendBytes, RecvBytes, RecvULong
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
    out = '\rProgress - %d%% [' % percent + '#' * percent + '.' * (100 - percent) + ']'
    print(out, end='')


@_cmd
def upload(sock: socket, path: str) -> bool:
    with open(path, 'rb') as f:
        bts = f.read()
    SendBytes(sock, bts, True)
    return RecvResponse(sock) == SUCCESS


@_cmd
def download(sock: socket, path: str) -> bool:
    chunks = RecvULong(sock)
    print_progress(0)
    with open(path, 'wb') as f:
        SendSignal(sock)
        for i in range(chunks):
            f.write(RecvBytes(sock))
            print_progress((i + 1) / chunks)
    print()  # new line
    return True
