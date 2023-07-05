from Shell import shell, Command, User
from ipaddress import IPv4Address, AddressValueError
import socket
import VFS

Server = None  # is set in main


def check_path(path: str) -> bool:
    if VFS.check(path):
        return False
    print(f'\'%s\' is not a valid path. Path must not contain next character sequences: \'%s\''
          % (path, '\', \''.join(VFS.BadChars)))
    return True


def _cd(args: list):
    path = args[0]
    if check_path(path): return
    if not VFS.cd(path):
        print(f'\'%s\' is not a directory' % path)


def _ls(args: list):
    path = args[0]
    if check_path(path): return
    entities = VFS.ls(path)
    if entities is None:
        print(f'\'%s\' is not a directory' % path)
    else:
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


def create(path: str, isDir: bool):
    if check_path(path): return
    if not VFS.add(path, isDir):
        print(f'\'%s\' already exists or some path elements are files' % path)


def remove(args: list):
    path = args[0]
    if check_path(path): return
    if not VFS.isempty(path):
        confirm = input(f'\'%s\' is not empty. Are you sure? [Y\\n]: ' % path).lower()
        if confirm != 'y': return
    if not VFS.remove(path):
        print(f'\'%s\' does not exist or cannot be removed' % path)


def _abs(args: list):
    path = args[0]
    if check_path(path): return
    if VFS.exists(path):
        print(VFS.absPath(path))
    else:
        print(f'\'%s\' does not exist' % path)


Command('exit', 0, (), lambda args: exit(0))
Command('cd', 1, (str,), _cd)
Command('ls', 0, (), lambda args: _ls(['.']))
Command('lsp', 1, (str,), _ls)
Command('mkfile', 1, (str,), lambda args: create(args[0], False))
Command('mkdir', 1, (str,), lambda args: create(args[0], True))
Command('rm', 1, (str,), remove)
Command('abs', 1, (str,), _abs)
# Command('rmfile', 1, (str,), remove)
# Command('rmdir', 1, (str,), remove)

Command('download', 2, (str, str), lambda args: None)
Command('upload', 2, (str, str), lambda args: None)
Command('cpfile', 2, (str, str), lambda args: None)
Command('mvfile', 2, (str, str), lambda args: None)
Command('format', 0, (), lambda args: None)


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
    # main()
    shell(prompt)
