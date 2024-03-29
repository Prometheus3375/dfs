import functools
import os
import os.path as ospath
import shutil
from threading import RLock
from time import sleep

root_dir = 'storage'
sep = '/'
_locker = RLock()


def _lock(func):
    @functools.wraps(func)
    def wrapper(*args):
        with _locker:
            return func(*args)

    return wrapper


def _create_dir(path: str):
    if ospath.isfile(path):
        os.remove(path)
    if not ospath.exists(path):
        os.mkdir(path)


_create_dir(root_dir)


def _remove_dir(path: str):
    shutil.rmtree(path, True)


def _remove(path: str):
    if ospath.isfile(path):
        os.remove(path)
    elif ospath.isdir(path):
        _remove_dir(path)


@_lock
def GetNameList(path: str) -> list:
    root, this = ospath.split(path.rstrip(sep))
    names = [this] if this else []
    while root:
        root, this = ospath.split(root.rstrip(sep))
        if this: names.append(this)
    return names[::-1]


def _convert_path(path: str) -> str:
    return root_dir + path if path[0] == sep else root_dir + sep + path


@_lock
def GetValidPath(path: str) -> str:
    return _convert_path(path)


@_lock
def Exists(path: str) -> bool:
    path = _convert_path(path)
    return ospath.isdir(path)


@_lock
def Create(path: str) -> str:
    path = _convert_path(path)
    names = GetNameList(path)
    path = ''
    for name in names:
        path += name + sep
        _create_dir(path)
    return path


@_lock
def CreateFile(path: str):
    path = Create(path)
    if os.listdir(path):
        _remove(path)
        # Small pause before recreating, without it OSError invoked randomly
        sleep(0.1)
        os.mkdir(path)
    return path


@_lock
def Remove(path: str):
    path = _convert_path(path)
    _remove(path)


@_lock
def Rename(path: str, name: str):
    path = _convert_path(path)
    parent, _ = ospath.split(path)
    newpath = ospath.join(parent, name)
    _remove(newpath)
    os.rename(path, newpath)


@_lock
def Move(what: str, to: str):
    what = _convert_path(what)
    _, name = ospath.split(what)
    to = ospath.join(Create(to), name)
    shutil.move(what, to)


@_lock
def Copy(what: str, to: str):
    what = _convert_path(what)
    _, name = ospath.split(what)
    to = ospath.join(Create(to), name)
    shutil.copytree(what, to)


@_lock
def Flush():
    _remove_dir(root_dir)
    # Small pause before recreating, without it OSError invoked randomly
    sleep(0.1)
    os.mkdir(root_dir)


@_lock
def GetFreeSpace() -> int:
    total, used, free = shutil.disk_usage('.')
    return free


def _get_dir_size(path: str) -> int:
    space = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            space += _get_dir_size(entry.path)
        else:
            space += entry.stat(follow_symlinks=False).st_size
    return space


@_lock
def GetSize(path: str) -> int:
    path = _convert_path(path)
    return _get_dir_size(path)


@_lock
def GetStats(path: str) -> tuple:
    path = _convert_path(path)
    return _get_dir_size(path), ospath.getatime(path), ospath.getctime(path), ospath.getmtime(path)
