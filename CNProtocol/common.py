from Common.Misc import EnumCode, MyException

RemoteCommands = EnumCode()

Command_Update = RemoteCommands('update')
Command_Flush = RemoteCommands('flush')
Command_MKFile = RemoteCommands('make file')
Command_MKDir = RemoteCommands('make dir')
Command_Remove = RemoteCommands('remove')
Command_Rename = RemoteCommands('rename')
Command_Move = RemoteCommands('move')
Command_Copy = RemoteCommands('copy')
Command_Info = RemoteCommands('info')
Command_Download = RemoteCommands('download')
Command_Upload = RemoteCommands('upload')

SUCCESS = ''


class CNPException(MyException):
    pass


Update_LineSeparator = '\n'
