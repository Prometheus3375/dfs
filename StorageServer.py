from threading import Thread

import SProtocol.NSP.storage as NSP
import SProtocol.storage as SP
import SServer.Jobs as Jobs
from Common.AskInput import GetIPOrDomain
from Common.Constants import StorageServerPort, TEST
from Common.Logger import ServerLogger
from Common.Socket import BindAndListen, Accept, socket, SocketError

LogPath = 'Slog.txt'
Logger = ServerLogger(LogPath, not TEST)
MainSocket: socket = ...
IPPath = 'myip.txt'


def serve(sock: socket, host: tuple):
    host = '%s:%d' % host
    Logger.add(host + ' has connected')
    try:
        SP.Serve(sock, Logger)
    except SocketError as e:
        Logger.addError('A socket error occurred during serving %s' % host, e)
    except SP.SPException as e:
        Logger.addError('A protocol error occurred during serving %s' % host, e)
    except OSError as e:
        Logger.addError('An OS error occurred during serving %s' % host, e)
    except Exception as e:
        Logger.addError('A unknown error occurred during serving %s' % host, e)
    finally:
        Logger.add(host + ' has disconnected')
        Jobs.AbortJob(sock)
        sock.close()


def SetPublicIP():
    ip = GetIPOrDomain(IPPath, 'Input public IP address or domain name of this server')
    NSP.SetPublicIP(ip)


def incoming():
    global MainSocket
    MainSocket = BindAndListen('', StorageServerPort)
    print('Server started')
    while True:
        client_sock, addr = Accept(MainSocket)
        Thread(daemon=True, target=serve, args=(client_sock, addr)).start()


if __name__ == '__main__':
    try:
        SP.SetLogger(Logger)
        SetPublicIP()
        incoming()
    except KeyboardInterrupt:
        Logger.add('Application was interrupted')
    except Exception as e:
        Logger.addError('An error occurred', e)
    finally:
        if isinstance(MainSocket, socket):
            MainSocket.close()
