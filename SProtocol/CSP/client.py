import functools

from Common.Constants import StorageServerPort
from Common.JobEx import SendJob
from Common.Socket import connection, SendBytesProgress, RecvBytesProgress
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


@_cmd
def upload(sock: socket, path: str) -> bool:
    with open(path, 'rb') as f:
        bts = f.read()
    SendBytesProgress(sock, bts)
    return RecvResponse(sock) == SUCCESS


@_cmd
def download(sock: socket, path: str) -> bool:
    bts = RecvBytesProgress(sock)
    with open(path, 'wb') as f:
        f.write(bts)
    return True
