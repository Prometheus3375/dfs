import socket
import os
import struct
from threading import Thread
import NServer.Database as DB
import NServer.Logger as Logger
Port = 8080


class Listener(Thread):
    def __init__(self, sock: socket.socket, addr: tuple):
        super().__init__(daemon=True)
        self.sock = sock
        self.ip, self.port = addr
        self.host = f'%s:%d' % addr
        Logger.add(self.host + ' has connected')
        sock.close()


def incoming():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', Port))
    sock.listen()
    while True:
        client_sock, addr = sock.accept()
        Listener(client_sock, addr)


def main():
    # Thread(daemon=True, target=incoming).start()
    incoming()


if __name__ == "__main__":
    main()
