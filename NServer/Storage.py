import functools
import os
from ipaddress import IPv4Network
from threading import RLock, Thread
from time import sleep

import SProtocol.NSP.server as NSP
from Common.Misc import Enum
from Common.Socket import SocketError
from Common.VFS import LockFS

FinderPeriod = 30  # in seconds
FinderNet = ...

_storages = {}
Statuses = Enum()
Status_Alive = Statuses()
Status_Dead = Statuses()
Status_Fixing = Statuses()
StorageData_BackUp = 'storage backup/'
if not os.path.exists(StorageData_BackUp):
    os.mkdir(StorageData_BackUp)

_locker = RLock()


def _lock(func):
    @functools.wraps(func)
    def wrapper(*args):
        with _locker:
            return func(*args)

    return wrapper


@_lock
def SetNet(net: str):
    global FinderNet
    FinderNet = IPv4Network(net)


class Storage(LockFS):
    def __init__(self, ip: str, pubip: str):
        super().__init__()
        self.lock = _locker
        self.ip = ip
        _storages[ip] = self
        self.status = Status_Alive
        self.pubip = pubip
        self.backup_path = StorageData_BackUp + ip
        self.loadFS()

    def loadFS(self):
        if os.path.exists(self.backup_path):
            with open(self.backup_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.fillFromLines(lines)

    def saveFS(self):
        lines = self.walkWithTypes()
        with open(self.backup_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    def isAlive(self) -> bool: return self.status == Status_Alive

    def isDead(self) -> bool: return self.status == Status_Dead

    def isFixing(self) -> bool: return self.status == Status_Fixing


def _update(ip: str, pubip: str):
    if ip in _storages:
        _storages[ip].pubip = ip
    else:
        Storage(ip, pubip)


@_lock
def FindStorages():
    for addr in FinderNet.hosts():
        try:
            ip = str(addr)
            pubip = NSP.locate(ip)
            _update(ip, pubip)
        except SocketError:
            pass


def FinderThread():
    sleep(FinderPeriod)
    while True:
        FindStorages()
        sleep(FinderPeriod)


def StartFinder():
    FindStorages()
    Thread(daemon=True, target=FinderThread).start()


@_lock
def GetAliveServers() -> list:
    return [ip for ip in _storages if _storages[ip].isAlive()]


def GetStorage(ip: str) -> LockFS:
    return _storages[ip]


@_lock
def SaveStorageData():
    for stor in _storages.values():
        stor.saveFS()
