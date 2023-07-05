from Common.Misc import EnumCode
from Common.Socket import SendInt, RecvInt, socket, SendStr, RecvStr, SleepTime
from SProtocol.common import SPException

Commands = EnumCode()
CommandType = int

Cmd_Locate = Commands('locate')
Cmd_MKFile = Commands('make file')
Cmd_Remove = Commands('remove')
Cmd_Rename = Commands('rename')
Cmd_Move = Commands('move')
Cmd_Copy = Commands('copy')
Cmd_Flush = Commands('flush')
Cmd_Info = Commands('info')
Cmd_Upload = Commands('upload')
Cmd_Download = Commands('download')
Cmd_PrepareReplicate = Commands('prep replicate')
Cmd_DoReplicate = Commands('do replicate')

LocateTimeout = SleepTime * 3  # in seconds
InfoSeparator = '\n'
LoadTimeout = 60  # in seconds
PathSeparator = '\n'

ResponseType = str
SUCCESS = ''


class NSPException(SPException):
    pass


def SendCommand(sock: socket, cmd: CommandType):
    SendInt(sock, cmd)


def RecvCommand(sock: socket) -> CommandType:
    return RecvInt(sock)


def SendResponse(sock: socket, re: ResponseType):
    SendStr(sock, re)


def RecvResponse(sock: socket) -> ResponseType:
    return RecvStr(sock)
