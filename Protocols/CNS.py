from Common.Misc import Enum

ProtocolV = 1
Commands = Enum(0)

Command_Update = Commands.new()
Command_Flush = Commands.new()
Command_MKFile = Commands.new()
Command_MKDir = Commands.new()
Command_Remove = Commands.new()
Command_Rename = Commands.new()
Command_Move = Commands.new()
Command_Copy = Commands.new()
Command_Download = Commands.new()
Command_Upload = Commands.new()
