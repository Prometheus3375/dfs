import getpass
import os
import platform

from .Misc import num2order

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
            cmd = args[0].lower()
            if cmd in Commands:
                Commands[cmd].run(args[1:])
            else:
                print('Unknown command \'' + cmd + '\'')


class Command:
    def __init__(self, name: str, args_n: tuple, arg_types: tuple, funcs: tuple):
        # Check number of args, number of types number of funcs
        l = len(args_n)
        if l != len(arg_types):
            raise ValueError('Lengths of arguments number and types tuples mismatch')
        if l != len(funcs):
            raise ValueError('Lengths of arguments number and function tuples mismatch')
        # Check the number of args and the number of types
        for n, types in zip(args_n, arg_types):
            if n != len(types):
                raise ValueError(f'The number of types for arguments of command \'%s\' must be %d, got %d'
                                 % name, n, len(types))
        # Add command
        self.args_n = list(args_n)
        self.args_n.sort()
        self.arg_types = {n: types for n, types in zip(args_n, arg_types)}
        self.funcs = {n: func for n, func in zip(args_n, funcs)}
        # Make invalid argument number error message
        if l > 1:
            args_n = [str(i) for i in self.args_n]
            self.ian = f'Possible number of arguments for command \'%s\': ' % name + ', '.join(args_n)
        else:
            args_n = args_n[0]
            if args_n == 0:
                self.ian = f'Command \'%s\' requires no arguments' % name
            elif args_n == 1:
                self.ian = f'Command \'%s\' requires 1 argument' % name
            else:
                self.ian = f'Command \'%s\' requires %d arguments' % (name, args_n)
        # Add command to dict
        Commands[name] = self

    @staticmethod
    def add(name: str, args_n: int, arg_types: tuple, func):
        if name in Commands:
            cmd = Commands[name]
            if args_n in cmd.args_n:
                raise ValueError('Command \'%s\' already has settings for %d argument(s)' % (name, args_n))
            else:
                args_n = (*cmd.args_n, args_n)
                arg_types = (*[cmd.arg_types[i] for i in cmd.args_n], arg_types)
                funcs = (*[cmd.funcs[i] for i in cmd.args_n], func)
                return Command(name, args_n, arg_types, funcs)
        return Command(name, (args_n,), (arg_types,), (func,))

    @staticmethod
    def zero(name: str, func):
        return Command.add(name, 0, (), func)

    @staticmethod
    def one(name: str, argtype, func):
        return Command.add(name, 1, (argtype,), func)

    def run(self, args: list):
        # Check the number of arguments
        l = len(args)
        if not (l in self.args_n):
            print(self.ian)
            return
        # Check the type of arguments
        types = self.arg_types[l]
        if types:
            for i in range(l):
                try:
                    args[i] = types[i](args[i])
                except ValueError:
                    print(f'Type of the %s argument must be %s' % (num2order(i + 1), types[i].__name__))
                    return
        # Run command function
        self.funcs[l](*args)
