from Shell import shell, Command, User
from ipaddress import IPv4Address, AddressValueError
import socket
import VFS

Server = None  # is set in main


def checkPath(path: str) -> bool:
    if VFS.badPath(path):
        print(f'\'%s\' is not a valid path. Path must not contain next character sequences: \'%s\''
              % (path, '\', \''.join(VFS.BadPathChars)))
        return True
    return False


def checkName(path: str) -> bool:
    if VFS.badName(path):
        print(f'\'%s\' is not a valid name. Name must not contain next character sequences: \'%s\''
              % (path, '\', \''.join(VFS.BadNameChars)))
        return True
    return False


def noPath(path: str) -> bool:
    if VFS.exists(path):
        return False
    print(f'\'%s\' does not exist' % path)
    return True


def _cd(args: list):
    path = args[0]
    if checkPath(path) or noPath(path): return
    try:
        VFS.cd(path)
    except VFS.VFSException as e:
        print(e)


def _ls(args: list):
    path = args[0]
    if checkPath(path) or noPath(path): return
    try:
        entities = VFS.ls(path)
    except VFS.VFSException as e:
        print(e)
        return
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
    path = args[0]
    if checkPath(path) or noPath(path): return
    print(VFS.absPath(path))


def _format(args: list):
    VFS.format()


def create(path: str, isDir: bool):
    if checkPath(path): return
    try:
        VFS.add(path, isDir)
    except VFS.VFSException as e:
        print(e)
        return


def remove(args: list):
    path = args[0]
    if checkPath(path) or noPath(path): return
    path = VFS.absPath(path)
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
    try:
        VFS.remove(path)
    except VFS.VFSException as e:
        print(e)
        return


def _rename(args: list):
    what, name = args
    if checkPath(what) or checkName(name) or noPath(what): return
    try:
        VFS.rename(what, name)
    except VFS.VFSException as e:
        print(e)
        return


def _move(args: list):
    what, to = args
    if checkPath(what) or checkPath(to) or noPath(what): return
    what = VFS.absPath(what)
    if VFS.isroot(what):
        print(f'Root directory cannot be moved')
        return
    if VFS.isparent(what):
        print(f'\'%s\' cannot be moved from current working directory' % what)
        return
    try:
        VFS.move(what, to)
    except VFS.VFSException as e:
        print(e)
        return


def _copy(args: list):
    what, to = args
    if checkPath(what) or checkPath(to) or noPath(what): return
    try:
        VFS.copy(what, to)
    except VFS.VFSException as e:
        print(e)
        return


Command.zero('exit', lambda args: exit(0))
Command.one('cd', str, _cd)
Command.zero('ls', lambda args: _ls(['.']))
Command.one('ls', str, _ls)
Command.one('abs', str, _abs)
Command.zero('walk', lambda args: print(*VFS.walk(), sep='\n'))

Command.zero('format', _format)
Command.one('mkfile', str, lambda args: create(args[0], False))
Command.one('mkdir', str, lambda args: create(args[0], True))
Command.one('rm', str, remove)
Command.single('re', 2, (str, str), _rename)
Command.single('mv', 2, (str, str), _move)
Command.single('cp', 2, (str, str), _copy)

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
