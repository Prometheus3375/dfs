from Common.Misc import EnumCode, MyException
from Common.Socket import socket, SendInt, SendStr, RecvInt, RecvStr

RemoteCommands = EnumCode()
RCType = int

Command_Update = RemoteCommands('update')
Command_MKFile = RemoteCommands('make file')
Command_MKDir = RemoteCommands('make dir')
Command_Remove = RemoteCommands('remove')
Command_Rename = RemoteCommands('rename')
Command_Move = RemoteCommands('move')
Command_Copy = RemoteCommands('copy')
Command_Flush = RemoteCommands('flush')
Command_Info = RemoteCommands('info')
Command_Upload = RemoteCommands('upload')
Command_Download = RemoteCommands('download')

Update_LineSeparator = '\n'
InfoSeparator = '\n'

ResponseType = str
SUCCESS = ''
UploadFail = f'Uploading of \'%s\' failed'


class CNPException(MyException):
    pass


def SendCommand(sock: socket, cmd: RCType):
    SendInt(sock, cmd)


def RecvCommand(sock: socket) -> RCType:
    return RecvInt(sock)


def SendResponse(sock: socket, re: ResponseType):
    SendStr(sock, re)


def RecvResponse(sock: socket) -> ResponseType:
    return RecvStr(sock)
