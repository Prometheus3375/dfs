from datetime import datetime

import CNProtocol.сlient as CNP
from Common.Constants import *
from Common.Shell import shell, Command, User
from Common.Socket import SocketError, Error_Other, CheckIP
from Common.VFS import FileSystem, VFSException, Node, Dir

FS = FileSystem()
Server = ...  # is set in SetServer
CallVFSOutput = ...  # is set in CallVFS
CallCNPOutput = ...  # is set in CallCNP
DateTimeFormat = '%c'


def CallVFS(func, *args):
    try:
        global CallVFSOutput
        CallVFSOutput = func(*args)
    except VFSException as e:
        print(e)
        return True
    return False


# region No connect
def changeCWD(path: str):
    CallVFS(FS.cd, path)


def listDir(path: str):
    if CallVFS(FS.ls, path):
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
    if not CallVFS(FS.absPath, path):
        print(CallVFSOutput)


# endregion
# region With connect
def CallCNP(func, *args, print_response: bool = True) -> bool:
    """
    :param func: function to call
    :param args: additional arguments of function
    :param print_response: print response of func or not
    :return: True if an error occurs, False otherwise
    """
    try:
        re = func(Server, *args)
        if re and print_response: print(re)
        global CallCNPOutput
        CallCNPOutput = re
        return False
    except SocketError as e:
        if e.code == Error_Other:
            print('Unknown error occurred:', e)
        else:
            print('Error occurred:', e)
    except CNP.CNPException as e:
        print('Error occurred:', e)
    return True


def update():
    if not CallCNP(CNP.update, print_response=False):
        paths_types = CallCNPOutput
        FS.flush()
        FS.fillFromLines(paths_types)


def create(path: str, isDir: bool):
    if path == FS.RootPath:
        print('Root directory already exists')
        return
    if CallVFS(FS.add, path, isDir):
        return
    # All OK, call remote
    node: Node = CallVFSOutput
    path = node.getPath()
    if CallCNP(CNP.create, path, isDir):
        node.delete()


def remove(path: str):
    try:
        node = FS.nodeAt(path)
        path = node.getPath()
        if node.isRoot:
            print('Root directory cannot be removed')
            return
        if node.isDir:
            # noinspection PyTypeChecker
            if FS.isCWDAncestor(node):
                print('\'%s\' cannot be removed from current working directory' % path)
                return
            # noinspection PyUnresolvedReferences
            if not node.isEmpty():
                confirm = input('\'%s\' is not empty. Are you sure? [Y\\n]: ' % path).lower()
                if confirm != 'y':
                    print('Operation aborted')
                    return
        parent: Dir = node.parent
        node.delete()
    except VFSException as e:
        print(e)
        return
    # All OK, call remote
    if CallCNP(CNP.remove, path):
        parent.add(node.name, node.isDir)


def rename(what: str, name: str):
    # if CallVFS(FS.rename, what, name):
    #     return
    try:
        node = FS.nodeAt(what)
        what = node.getPath()
        if node.isDir:
            print('\'%s\' is a directory, renaming directories is not supported yet' % what)
            return
        oldname = node.name
        node.rename(name)
    except VFSException as e:
        print(e)
        return
    if CallCNP(CNP.rename, what, name):
        node.rename(oldname)


def move(what: str, to: str):
    try:
        node = FS.nodeAt(what)
        what = node.getPath()
        if node.isRoot:
            print('Root directory cannot be removed')
            return
        if node.isDir:
            print('\'%s\' is a directory, moving directories is not supported yet' % what)
            return
        # if node.isDir and FS.isCWDAncestor(node):
        #     print('\'%s\' cannot be moved from current working directory' % what)
        #     return
        oldparent = node.parent
        FS.moveNode(node, to)
    except VFSException as e:
        print(e)
        return
    if CallCNP(CNP.move, what, to):
        FS.moveNode(node, oldparent)


def copy(what: str, to: str):
    # if CallVFS(FS.copy, what, to):
    #     return
    try:
        node = FS.nodeAt(what)
        what = node.getPath()
        if node.isDir:
            print('\'%s\' is a directory, copying directories is not supported yet' % what)
            return
        node = FS.copyNode(node, to)
    except VFSException as e:
        print(e)
        return
    if CallCNP(CNP.copy, what, to):
        node.delete()


def flush():
    if not CallCNP(CNP.flush, print_response=False):
        FS.flush()
        print(f'Available space: {CallCNPOutput // (2 ** 30)} GiB')


def info(path: str):
    # if CallVFS(FS.nodeAt, path):
    #     return
    try:
        node = FS.nodeAt(path)
        path = node.getPath()
        if node.isDir:
            print('\'%s\' is a directory, getting info of directories is not supported yet' % path)
            return
    except VFSException as e:
        print(e)
        return
    if not CallCNP(CNP.info, path, print_response=False):
        re = CallCNPOutput
        if isinstance(re, str):
            print(re)
            return
        stats: list = CallCNPOutput
        size = int(stats[0])
        atime = datetime.fromtimestamp(float(stats[1]))
        ctime = datetime.fromtimestamp(float(stats[2]))
        mtime = datetime.fromtimestamp(float(stats[3]))
        print(f'Size - {size // (2 ** 20)} MiB\n'
              f'Last access time - {atime.strftime(DateTimeFormat)}\n'
              f'Last meta change time - {ctime.strftime(DateTimeFormat)}\n'
              f'Last modification time - {mtime.strftime(DateTimeFormat)}\n'
              )


# endregion
# region Commands
Command.zero('exit', lambda: exit(0))
Command.one('cd', str, changeCWD)
Command.zero('ls', lambda: listDir('.'))
Command.one('ls', str, listDir)
Command.one('abs', str, absPath)
Command.zero('walk', lambda: print(*FS.walk(), sep='\n'))

Command.zero('update', update)
Command.one('mkfile', str, lambda path: create(path, False))
Command.one('mkdir', str, lambda path: create(path, True))
Command.one('rm', str, remove)
Command.add('re', 2, (str, str), rename)
Command.add('mv', 2, (str, str), move)
Command.add('cp', 2, (str, str), copy)

Command.zero('flush', flush)
Command.one('info', str, info)
Command.add('upload', 2, (str, str), lambda real, virt: None)
Command.add('download', 2, (str, str), lambda virt, real: None)


# endregion


def SetServer():
    while True:
        ip = 'localhost' if TEST else input('Input DFS server IP address or domain name: ').strip()
        # Check IP or domain
        ip = CheckIP(ip)
        if ip: break
        print('Error: \'%s\' - no such IP or domain' % ip)
    global Server
    Server = ip, NameServerClientPort


def main():
    # Get remote
    SetServer()
    # Get VFS
    update()
    # Start shell
    shell(lambda: User + ':' + FS.CWDPath + '$ ')


if __name__ == '__main__':
    try:
        main()
        # shell(prompt)
    except KeyboardInterrupt:
        pass
