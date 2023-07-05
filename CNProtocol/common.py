from Common.Misc import Enum, MyException

RemoteCommands = Enum(0)

Command_Update = RemoteCommands()
Command_Flush = RemoteCommands()
Command_MKFile = RemoteCommands()
Command_MKDir = RemoteCommands()
Command_Remove = RemoteCommands()
Command_Rename = RemoteCommands()
Command_Move = RemoteCommands()
Command_Copy = RemoteCommands()
Command_Download = RemoteCommands()
Command_Upload = RemoteCommands()


class CNPException(MyException):
    pass


Update_LineSeparator = '\n'
