from Shell import shell, Command, User
from ipaddress import IPv4Address, AddressValueError
import socket
import VFS

Server = None  # is set in main
CallVFSOutput = None  # is set in CallVFS


def CallVFS(func, args):
    try:
        global CallVFSOutput
        CallVFSOutput = func(*args)
    except VFS.VFSException as e:
        print(e)
        return True
    return False


def _cd(args: list):
    CallVFS(VFS.cd, args)


def _ls(args: list):
    if CallVFS(VFS.ls, args):
        return
    entities = CallVFSOutput
    names, types = entities
    if names:
        namesl = [len(name) for name in names]
        indent = max(namesl)
        indent = max(4, indent) + 3
        print('Name' + ' ' * (indent - 4) + 'Type')
        print('-' * (indent + 4))
        for name, namel, typ in zip(names, namesl, types):
            print(name + ' ' * (indent - namel) + ('file' if typ else 'dir'))
    else:
        print('Name   Type')
        print('-----------')


def _abs(args: list):
    if not CallVFS(VFS.absPath, args):
        print(CallVFSOutput)


def format(args: list):
    VFS.format()


def create(path: str, isDir: bool):
    if path == VFS.RootPath:
        print(f'Root directory already exists')
        return
    if CallVFS(VFS.add, (path, isDir)):
        return


def remove(args: list):
    path = args[0]
    try:
        if VFS.isroot(path):
            print(f'Root directory cannot be removed')
            return
        if VFS.isparent(path):
            print(f'\'%s\' cannot be removed from current working directory' % path)
            return
        if not VFS.isempty(path):
            confirm = input(f'\'%s\' is not empty. Are you sure? [Y\\n]: ' % path).lower()
            if confirm != 'y':
                print('Operation aborted')
                return
        VFS.remove(path)
    except VFS.VFSException as e:
        print(e)
        return


def rename(args: list):
    what, to = args
    if CallVFS(VFS.rename, (what, to)):
        return


def move(args: list):
    what, to = args
    try:
        if VFS.isroot(what):
            print(f'Root directory cannot be moved')
            return
        if VFS.isparent(what):
            print(f'\'%s\' cannot be moved from current working directory' % what)
            return
        VFS.move(what, to)
    except VFS.VFSException as e:
        print(e)
        return


def copy(args: list):
    what, to = args
    if CallVFS(VFS.copy, (what, to)):
        return


Command.zero('exit', lambda args: exit(0))
Command.one('cd', str, _cd)
Command.zero('ls', lambda args: _ls(['.']))
Command.one('ls', str, _ls)
Command.one('abs', str, _abs)
Command.zero('walk', lambda args: print(*VFS.walk(), sep='\n'))

Command.zero('format', format)
Command.one('mkfile', str, lambda args: create(args[0], False))
Command.one('mkdir', str, lambda args: create(args[0], True))
Command.one('rm', str, remove)
Command.single('re', 2, (str, str), rename)
Command.single('mv', 2, (str, str), move)
Command.single('cp', 2, (str, str), copy)

Command.single('download', 2, (str, str), lambda args: None)
Command.single('upload', 2, (str, str), lambda args: None)


def prompt() -> str:
    return User + ':' + VFS.cwdPath() + '$ '


def main():
    while True:
        ip, port = input('Input DFS server IP address and port: ').strip().split(' ')
        # Check IP or domain
        try:
            IPv4Address(ip)
        except AddressValueError:
            try:
                ip = socket.gethostbyname(ip)
            except socket.error:
                print('Error: \'%s\' - no such IP or domain' % ip)
                continue
        # Check port
        try:
            port = int(port)
        except ValueError:
            print('Error: \'%s\' is invalid port number' % port)
            continue
        break
    host = ip + ':' + str(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Check connection
        try:
            s.connect((ip, port))
        except socket.error:
            print('Error: cannot connect to ' + host)
            return
        # Set socket
        global Server
        Server = s
        # Start shell
        shell(prompt)


if __name__ == '__main__':
    try:
        # main()
        shell(prompt)
    except KeyboardInterrupt:
        pass
