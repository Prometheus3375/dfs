from threading import Thread, Lock

import CNProtocol.server as CNP
import SProtocol.NSP.server as NSP
from Common.Constants import NameServerClientPort, TEST
from Common.Logger import ServerLogger
from Common.Socket import CheckNet
from Common.Socket import socket, SocketError, BindAndListen, Accept
from Common.VFS import VFSException
from NServer.FileSystems import SaveActual, LoadActual
from NServer.Storage import SaveStorageData, StartFinder, SetNet

LogFile = 'Nlog.txt'
Logger = ServerLogger(LogFile, not TEST)
SafeLock = Lock()  # One user at a time
ClientSocket = ...  # set in incoming


class Listener(Thread):
    def __init__(self, sock: socket, addr: tuple):
        super().__init__(daemon=True)
        self.sock = sock
        self.ip, self.port = addr
        self.host = '%s:%d' % addr
        Logger.add(self.host + ' has connected')

    def run(self):
        with SafeLock:
            sock = self.sock
            try:
                CNP.ServeClient(sock)
            except SocketError as e:
                Logger.add('A socket error occurred during serving %s: ' % self.host + str(e))
            except CNP.CNPException as e:
                Logger.add('A protocol error occurred during serving %s: ' % self.host + str(e))
            except VFSException as e:
                Logger.add('A VFS error occurred during serving %s: ' % self.host + str(e))
            except Exception as e:
                Logger.add('A unknown error occurred during serving %s: ' % self.host + str(e))
            finally:
                Logger.add(self.host + ' has disconnected')
                sock.close()


def SetLocalNet():
    while True:
        net = '127.0.0.0/31' if TEST else input('Input network address where storages are situated: ').strip()
        # Check IP or domain
        res = CheckNet(net)
        if not res:
            break
        print(res)
    SetNet(net)


def incoming():
    global ClientSocket
    ClientSocket = BindAndListen('', NameServerClientPort)
    print('Server started')
    while True:
        client_sock, addr = Accept(ClientSocket)
        Listener(client_sock, addr).start()


def main():
    CNP.SetLogger(Logger)
    NSP.SetLogger(Logger)
    LoadActual()
    SetLocalNet()
    StartFinder()
    # Thread(daemon=True, target=incoming).start()
    incoming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        Logger.add('Application was interrupted')
    except Exception as e:
        Logger.add('An error occurred: ' + str(e))
    finally:
        ClientSocket.close()
        SaveActual()
        SaveStorageData()
