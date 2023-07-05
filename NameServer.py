from threading import Thread

import CNProtocol.server as CNP
import NServer.Logger as Logger
from Common.Constants import *
from Common.Socket import SOL_SOCKET, SO_REUSEADDR, socket, AF_INET, SOCK_STREAM, SocketError


class Listener(Thread):
    def __init__(self, sock: socket, addr: tuple):
        super().__init__(daemon=True)
        self.sock = sock
        self.ip, self.port = addr
        self.host = '%s:%d' % addr
        Logger.add(self.host + ' has connected')

    def run(self):
        sock = self.sock
        try:
            CNP.RecvCommand(sock)
        except SocketError as e:
            Logger.add('A socket error occurred during serving %s: ' % self.host + str(e))
        except CNP.CNPException as e:
            Logger.add('A protocol error occurred during serving %s: ' % self.host + str(e))
        except Exception as e:
            Logger.add('A unknown error occurred during serving %s: ' % self.host + str(e))
        finally:
            Logger.add(self.host + ' has disconnected')
            sock.close()


def incoming():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('', NameServerClientPort))
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
