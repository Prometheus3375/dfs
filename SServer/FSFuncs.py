import functools
import os
import os.path as ospath
import shutil
from threading import RLock
from time import sleep

root_dir = 'storage'
sep = ospath.altsep
_locker = RLock()


def _lock(func):
    @functools.wraps(func)
    def wrapper(*args):
        with _locker:
            return func(*args)

    return wrapper


@_lock
def _create_dir(path: str):
    if ospath.isfile(path):
        os.remove(path)
    if not ospath.exists(path):
        os.mkdir(path)


_create_dir(root_dir)


@_lock
def _remove_dir(path: str):
    shutil.rmtree(path, True)


@_lock
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


@_lock
def _convert_path(path: str) -> str:
    return root_dir + path if path[0] == sep else root_dir + sep + path


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
    total, used, free = shutil.disk_usage('/')
    return free // (2 ** 30)
