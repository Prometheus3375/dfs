import functools
import os
from ipaddress import IPv4Network
from threading import RLock, Thread
from time import sleep

import SProtocol.NSP.server as NSP
from Common import Logger as _loggerclass
from Common.Misc import Enum
from Common.Socket import SocketError
from Common.VFS import LockFS

FinderPeriod = 30  # in seconds
FinderNet = ...
Logger = ...


def SetLogger(logger: _loggerclass):
    global Logger
    Logger = logger


_storages = {}
Statuses = Enum()
Status_Alive = Statuses()
Status_Dead = Statuses()
Status_Fixing = Statuses()
StorageData_BackUp = 'storage_backup/'
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
    def __init__(self, ip: str, pubip: str, space: int):
        super().__init__()
        self.lock = _locker
        self.ip = ip
        self.space = space
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


def _update(ip: str, pubip: str, space: int):
    if ip in _storages:
        store: Storage = _storages[ip]
        # Update storage data
        store.pubip = pubip
        store.space = space
        # Dead storage has come online
        if store.isDead():
            store.status = Status_Alive
            Logger.add('Storage %s has come online' % ip)
    else:
        Storage(ip, pubip, space)
        Logger.add('Added new storage %s' % ip)


@_lock
def FindStorages():
    is31 = str(FinderNet.netmask) == '255.255.255.254'
    for addr in FinderNet.hosts():
        ip = str(addr)
        # IPv4Network(x.y.z.0/m).hosts() with m == 31 returns x.y.z.0 and x.y.z.1 instead of only x.y.z.1
        # Do not locate x.y.z.0
        if is31 and ip[-1] == '0': continue
        try:
            # Locate storage
            pubip, space = NSP.locate(ip)
            # Update info
            _update(ip, pubip, space)
        except SocketError:
            # A storage is lost
            if ip in _storages:
                store: Storage = _storages[ip]
                # Mark as dead
                store.status = Status_Dead
                Logger.add('Storage %s has gone offline' % ip)
                # Replicate everything from dead storage
                paths = store.walkFiles()
                NSP.Replicate(paths)


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
    alive = [store for store in _storages.values() if store.isAlive()]
    alive.sort(key=lambda x: x.space, reverse=True)
    return [store.ip for store in alive]


@_lock
def GetASWithPath(path: str) -> list:
    alive = []
    for fs in _storages.values():
        if fs.isAlive() and path in fs:
            alive.append(fs)
    alive.sort(key=lambda x: x.space, reverse=True)
    return [store.ip for store in alive]


@_lock
def GetASNoPath(path: list) -> list:
    alive = []
    for fs in _storages.values():
        if fs.isAlive() and path not in fs:
            alive.append(fs)
    alive.sort(key=lambda x: x.space, reverse=True)
    return [store.ip for store in alive]


@_lock
def GetStorage(ip: str) -> Storage:
    return _storages[ip]


@_lock
def SaveStorageData():
    for stor in _storages.values():
        stor.saveFS()
