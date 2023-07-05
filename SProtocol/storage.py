import SProtocol.CSP.storage as CSP
import SProtocol.NSP.storage as NSP
import SProtocol.SSP.storage_client as SSPc
import SProtocol.SSP.storage_server as SSPs
from Common.Logger import Logger
from SProtocol.common import *

_wmi2func = {
    NameServer: NSP.ServeNameServer,
    Client: CSP.ServeClient,
    StorageServer: SSPs.ServeStorage
}


def Serve(sock: socket, logger: Logger):
    wmi = RecvWMI(sock)
    if wmi in WhoAmI:
        logger.addHost(*sock.getpeername(), 'is ' + WhoAmI[wmi])
        _wmi2func[wmi](sock)
    else:
        # noinspection PyStringFormat
        raise SPException('Invalid WMI %d received from host %s:%d' % (wmi, *sock.getpeername()))


def SetLogger(logger: Logger):
    NSP.SetLogger(logger)
    CSP.SetLogger(logger)
    SSPc.SetLogger(logger)
    SSPs.SetLogger(logger)
