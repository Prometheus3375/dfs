import socket
from ipaddress import IPv4Address, AddressValueError

import CNSProtocol.сlient as NSP
from CNSProtocol import CNSError
from Common import *
from Common.Shell import shell, Command, User
from Common.Socket import SocketError, Error_Other
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


# region No connect
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


# endregion
# region With connect
def update():
    try:
        paths_types = NSP.update(Server)
        FS.fillFromLines(paths_types)
    except SocketError as e:
        if e.err == Error_Other:
            print('Unknown error occurred: ' + str(e))
        else:
            print('Failed to connect to server')
    except CNSError as e:
        print(e)


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


# endregion


Command.zero('exit', lambda: exit(0))
Command.one('cd', str, changeCWD)
Command.zero('ls', lambda: listDir('.'))
Command.one('ls', str, listDir)
Command.one('abs', str, absPath)
Command.zero('walk', lambda: print(*FS.walk(), sep='\n'))

Command.zero('update', update)
Command.zero('flush', lambda: flush)
Command.one('mkfile', str, lambda path: create(path, False))
Command.one('mkdir', str, lambda path: create(path, True))
Command.one('rm', str, remove)
Command.single('re', 2, (str, str), rename)
Command.single('mv', 2, (str, str), move)
Command.single('cp', 2, (str, str), copy)

Command.single('download', 2, (str, str), lambda virt, real: None)
Command.single('upload', 2, (str, str), lambda real, virt: None)


def prompt() -> str:
    return User + ':' + FS.CWDPath + '$ '


def main():
    while True:
        ip = input('Input DFS server IP address or domain name: ').strip()
        # Check IP or domain
        try:
            IPv4Address(ip)
        except AddressValueError:
            try:
                ip = socket.gethostbyname(ip)
            except socket.error:
                print('Error: \'%s\' - no such IP or domain' % ip)
                continue
        break
    global Server
    Server = ip, NameServerPort
    # Get VFS
    update()
    # Start shell
    shell(prompt)


if __name__ == '__main__':
    try:
        main()
        # shell(prompt)
    except KeyboardInterrupt:
        pass
