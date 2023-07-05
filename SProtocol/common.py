from Common.Misc import EnumCode, MyException
from Common.Socket import socket, SendInt, RecvInt

WhoAmI = EnumCode()
WMIType = int
Client = WhoAmI('client')
NameServer = WhoAmI('nameserver')
StorageServer = WhoAmI('storageserver')


class SPException(MyException):
    pass


def SendWMI(sock: socket, wmi: WMIType):
    SendInt(sock, wmi)


def RecvWMI(sock: socket) -> WMIType:
    return RecvInt(sock)
