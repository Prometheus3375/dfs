from Shell import shell, Command
from ipaddress import IPv4Address, AddressValueError
import socket


def _exit(args: list):
    if len(args) > 1:
        print('Command \'exit\' requires no arguments')
    else:
        exit(0)


Command('exit', 0, (), lambda args: exit(0))

Command('init', 0, (), lambda args: None)
Command('mkfile', 1, (str,), lambda args: None)
Command('download', 2, (str, str), lambda args: None)
Command('upload', 2, (str, str), lambda args: None)
Command('rmfile', 1, (str,), lambda args: None)
Command('cpfile', 2, (str, str), lambda args: None)
Command('mvfile', 2, (str, str), lambda args: None)
Command('cd', 1, (str,), lambda args: None)
Command('ls', 1, (str,), lambda args: None)
Command('mkdir', 1, (str,), lambda args: None)
Command('rmdir', 1, (str,), lambda args: None)


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
        shell()


if __name__ == '__main__':
    main()
