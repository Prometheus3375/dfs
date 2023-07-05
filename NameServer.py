from socket import SOL_SOCKET, SO_REUSEADDR
from threading import Thread

import NServer.Logger as Logger
from CNProtocol.server import *
from Common.Constants import *


class Listener(Thread):
    def __init__(self, sock: socket, addr: tuple):
        super().__init__(daemon=True)
        self.sock = sock
        self.ip, self.port = addr
        self.host = f'%s:%d' % addr
        Logger.add(self.host + ' has connected')

    def run(self):
        sock = self.sock
        try:
            RecvCommand(sock)
        except SocketError as e:
            Logger.add('A socket error occurred during serving %s: ' % self.host + str(e))
        except CNPException as e:
            Logger.add('A protocol error occurred during serving %s: ' % self.host + str(e))
        except Exception as e:
            Logger.add('A unknown error occurred during serving %s: ' % self.host + str(e))
        finally:
            Logger.add(self.host + ' has disconnected')
            sock.close()


def incoming():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('', NameServerPort))
    sock.listen()
    while True:
        client_sock, addr = sock.accept()
        Listener(client_sock, addr).start()


def main():
    # Thread(daemon=True, target=incoming).start()
    incoming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
