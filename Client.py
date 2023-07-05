from Common.Shell import shell, Command, User
from ipaddress import IPv4Address, AddressValueError
import socket
from Common.VFS import FileSystem, VFSException

FS = FileSystem()
Server = ...  # is set in main
CallVFSOutput = ...  # is set in CallVFS


def CallVFS(func, args):
    try:
        global CallVFSOutput
        CallVFSOutput = func(*args)
    except VFSException as e:
        print(e)
        return True
    return False


def changeCWD(path: str):
    CallVFS(FS.cd, (path,))


def listDir(path: str):
    if CallVFS(FS.ls, (path,)):
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


def absPath(path: str):
    if not CallVFS(FS.absPath, (path,)):
        print(CallVFSOutput)


def flush():
    FS.flush()


def create(path: str, isDir: bool):
    if path == FS.RootPath:
        print(f'Root directory already exists')
        return
    if CallVFS(FS.add, (path, isDir)):
        return


def remove(path: str):
    try:
        node = FS.nodeAt(path)
        path = node.getPath()
        if node.isRoot:
            print(f'Root directory cannot be removed')
            return
        if node.isDir:
            if FS.isCWDAncestor(node):
                print(f'\'%s\' cannot be removed from current working directory' % path)
                return
            if not node.isEmpty():
                confirm = input(f'\'%s\' is not empty. Are you sure? [Y\\n]: ' % path).lower()
                if confirm != 'y':
                    print('Operation aborted')
                    return
        node.delete()
    except VFSException as e:
        print(e)
        return


def rename(what: str, to: str):
    if CallVFS(FS.rename, (what, to)):
        return


def move(what: str, to: str):
    try:
        node = FS.nodeAt(what)
        what = node.getPath()
        if node.isRoot:
            print(f'Root directory cannot be removed')
            return
        if node.isDir and FS.isCWDAncestor(node):
            print(f'\'%s\' cannot be removed from current working directory' % what)
            return
        FS.moveNode(node, to)
    except VFSException as e:
        print(e)
        return


def copy(what: str, to: str):
    if CallVFS(FS.copy, (what, to)):
        return


Command.zero('exit', lambda: exit(0))
Command.one('cd', str, changeCWD)
Command.zero('ls', lambda: listDir('.'))
Command.one('ls', str, listDir)
Command.one('abs', str, absPath)
Command.zero('walk', lambda: print(*FS.walk(), sep='\n'))

Command.zero('flush', lambda: flush)
Command.one('mkfile', str, lambda path: create(path, False))
Command.one('mkdir', str, lambda path: create(path, True))
Command.one('rm', str, remove)
Command.single('re', 2, (str, str), rename)
Command.single('mv', 2, (str, str), move)
Command.single('cp', 2, (str, str), copy)

Command.zero('update', lambda: None)
Command.single('download', 2, (str, str), lambda virt, real: None)
Command.single('upload', 2, (str, str), lambda real, virt: None)


def prompt() -> str:
    return User + ':' + FS.CWDPath + '$ '


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
