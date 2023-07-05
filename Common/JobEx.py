from Common.Socket import socket, SendULong, RecvULong


def SendJob(sock: socket, job: int):
    SendULong(sock, job)


def RecvJob(sock: socket) -> int:
    return RecvULong(sock)
