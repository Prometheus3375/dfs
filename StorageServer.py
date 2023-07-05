from threading import Thread

import SProtocol.NSP.storage as NSP
import SProtocol.storage as SP
from Common.Constants import StorageServerPort, TEST
from Common.Logger import ServerLogger
from Common.Socket import BindAndListen, Accept, socket, SocketError, CheckIP

LogPath = 'Slog.txt'
Logger = ServerLogger(LogPath, not TEST)
MainSocket = ...


def serve(sock: socket, host: tuple):
    host = '%s:%d' % host
    try:
        SP.Serve(sock, Logger)
    except SocketError as e:
        Logger.add('A socket error occurred during serving %s: ' % host + str(e))
    except SP.SPException as e:
        Logger.add('A protocol error occurred during serving %s: ' % host + str(e))
    except Exception as e:
        Logger.add('A unknown error occurred during serving %s: ' % host + str(e))
    finally:
        Logger.add(host + ' has disconnected')
        sock.close()


def SetPublicIP():
    while True:
        ip = 'localhost' if TEST else input('Input public IP address or domain name of this server: ').strip()
        # Check IP or domain
        ip = CheckIP(ip)
        if ip: break
        print('Error: \'%s\' - no such IP or domain' % ip)
    NSP.SetPublicIP(ip)


def incoming():
    global MainSocket
    MainSocket = BindAndListen('', StorageServerPort)
    print('Server started')
    while True:
        client_sock, addr = Accept(MainSocket)
        Thread(target=serve, args=(client_sock, addr)).start()


if __name__ == '__main__':
    try:
        SP.SetLogger(Logger)
        SetPublicIP()
        incoming()
    except KeyboardInterrupt:
        Logger.add('Application was interrupted')
    except Exception as e:
        Logger.add('An error occurred: ' + str(e))
    finally:
        MainSocket.close()
