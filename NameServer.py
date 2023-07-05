from threading import Thread

import CNProtocol.server as CNP
from Common.Constants import NameServerClientPort, TEST
from Common.Logger import ServerLogger
from Common.Socket import socket, SocketError, BindAndListen, Accept

LogFile = 'log.txt'
Logger = ServerLogger(LogFile, not TEST)


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
            CNP.ServeClient(sock)
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
    sock = BindAndListen('', NameServerClientPort)
    while True:
        client_sock, addr = Accept(sock)
        Listener(client_sock, addr).start()


def main():
    # Thread(daemon=True, target=incoming).start()
    incoming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
