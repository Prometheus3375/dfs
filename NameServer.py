from threading import Lock, Thread

import CNProtocol.server as CNP
import NServer.Jobs as Jobs
import NServer.Storages as Storages
import SProtocol.NSP.server as NSP
from Common.AskInput import GetNet
from Common.Constants import NameServerClientPort, TEST
from Common.Logger import ServerLogger
from Common.Socket import socket, SocketError, BindAndListen, Accept
from Common.VFS import VFSException
from NServer.FileSystems import SaveActual, LoadActual

LogFile = 'Nlog.txt'
Logger = ServerLogger(LogFile, not TEST)
SafeLock = Lock()  # One user at a time
ClientSocket: socket = ...  # set in incoming
NetPath = 'storage_net.txt'


def serve(sock: socket, host: tuple):
    host = '%s:%d' % host
    Logger.add(host + ' has connected')
    with SafeLock:
        try:
            CNP.ServeClient(sock)
        except SocketError as e:
            Logger.addError('A socket error occurred during serving %s' % host, e)
        except CNP.CNPException as e:
            Logger.addError('Client-NameServer protocol error occurred during serving %s' % host, e)
        except NSP.NSPException as e:
            Logger.addError('NameServer-StorageServer protocol error occurred during serving %s' % host, e)
        except VFSException as e:
            Logger.addError('A VFS error occurred during serving %s' % host, e)
        except Exception as e:
            Logger.addError('A unknown error occurred during serving %s' % host, e)
        finally:
            Logger.add(host + ' has disconnected')
            Jobs.abort(sock)
            sock.close()


def SetLocalNet():
    net = GetNet(NetPath, 'Input network address where storages are situated')
    Storages.SetNet(net)


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
    Storages.SetLogger(Logger)
    LoadActual()
    SetLocalNet()
    Storages.StartFinder()
    # Thread(daemon=True, target=incoming).start()
    incoming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        Logger.add('Application was interrupted')
    except Exception as e:
        Logger.addError('An error occurred', e)
    finally:
        SaveActual()
        Storages.SaveData()
        if isinstance(ClientSocket, socket):
            ClientSocket.close()
