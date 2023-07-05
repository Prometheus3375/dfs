from Common.Misc import Enum, MyException

RemoteCommands = Enum(0)

Command_Update = RemoteCommands.new()
Command_Flush = RemoteCommands.new()
Command_MKFile = RemoteCommands.new()
Command_MKDir = RemoteCommands.new()
Command_Remove = RemoteCommands.new()
Command_Rename = RemoteCommands.new()
Command_Move = RemoteCommands.new()
Command_Copy = RemoteCommands.new()
Command_Download = RemoteCommands.new()
Command_Upload = RemoteCommands.new()


class CNPError(MyException):
    pass


Update_PTSep = '\n'
