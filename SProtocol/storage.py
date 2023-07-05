import SProtocol.CSP.storage as CSP
import SProtocol.NSP.storage as NSP
from Common.Logger import Logger
from SProtocol.common import *

_wmi2func = {NameServer: NSP.ServeNameServer, Client: CSP.ServeClient}


def Serve(sock: socket, logger: Logger):
    wmi = RecvWMI(sock)
    if wmi in WhoAmI:
        logger.addHost(*sock.getpeername(), 'is ' + WhoAmI[wmi])
        _wmi2func[wmi](sock)
    else:
        raise SPException('Invalid WMI received from host %s:%d' % sock.getpeername())


def SetLogger(logger: Logger):
    NSP.SetLogger(logger)
    CSP.SetLogger(logger)
