import getpass
import os
import platform
from Misc import num2order

User = str(getpass.getuser())
CWD = str(os.getcwd())
if platform.system() == 'Windows':
    Prompt = CWD + '>'
else:
    Prompt = User + ':' + CWD + '$ '
Commands = {}


def GetArgs(line: str) -> list:
    line = line.strip()
    dq = False
    sq = False
    args = []
    arg = ''
    for c in line:
        if c == ' ' and (not (dq or sq)):
            if arg:
                args.append(arg)
                arg = ''
        elif c == '"' and (not sq):
            dq = not dq
        elif c == '\'' and (not dq):
            sq = not sq
        else:
            arg += c
    if arg:
        args.append(arg)
    return args


def shell(prompt_func=lambda: Prompt):
    while True:
        line = input(prompt_func())
        args = GetArgs(line)
        if args:
            cmd = args[0]
            if cmd in Commands:
                Commands[cmd].run(args[1:])
            else:
                print('Unknown command \'' + cmd + '\'')


class Command:
    def __init__(self, name: str, args_n: int, arg_types: tuple, func):
        # Check name availability
        if name in Commands:
            raise ValueError(f'Command \'%s\' already exists' % name)
        # Check the number of args and the number of types
        if args_n != len(arg_types):
            raise ValueError(f'The number of types for arguments of command \'%s\' must be %d, got %d'
                             % name, args_n, len(arg_types))
        # Add command
        self.args_n = args_n
        self.arg_types = arg_types
        self.func = func
        if args_n == 0:
            self.ian = f'Command \'%s\' requires no arguments' % name
        elif args_n == 1:
            self.ian = f'Command \'%s\' requires 1 argument' % name
        else:
            self.ian = f'Command \'%s\' requires %d arguments' % (name, args_n)
        # Add command to dict
        Commands[name] = self

    def run(self, args: list):
        # Check the number of arguments
        l = len(args)
        if l != self.args_n:
            print(self.ian)
            return
        # Check the type of arguments
        if self.arg_types:
            for i in range(l):
                try:
                    args[i] = self.arg_types[i](args[i])
                except ValueError:
                    print(f'Type of the %s argument must be %s' % (num2order(i + 1), self.arg_types[i].__name__))
                    return
        # Run command function
        self.func(args)
