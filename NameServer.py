from threading import Lock, Thread

import CNProtocol.server as CNP
import NServer.Jobs as Jobs
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


def serve(sock: socket, host: tuple):
    host = '%s:%d' % host
    Logger.add(host + ' has connected')
    with SafeLock:
        try:
            CNP.ServeClient(sock)
        except SocketError as e:
            Logger.add('A socket error occurred during serving %s: ' % host + str(e))
        except CNP.CNPException as e:
            Logger.add('Client-NameServer protocol error occurred during serving %s: ' % host + str(e))
        except NSP.NSPException as e:
            Logger.add('NameServer-StorageServer protocol error occurred during serving %s: ' % host + str(e))
        except VFSException as e:
            Logger.add('A VFS error occurred during serving %s: ' % host + str(e))
        except Exception as e:
            Logger.add('A unknown error occurred during serving %s: ' % host + str(e))
        finally:
            Logger.add(host + ' has disconnected')
            Jobs.abort(sock)
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
        sock, addr = Accept(ClientSocket)
        Thread(daemon=True, target=serve, args=(sock, addr)).start()


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
