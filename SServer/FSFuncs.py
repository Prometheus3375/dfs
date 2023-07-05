import os
import os.path as ospath
import shutil

root_dir = 'storage'
sep = ospath.altsep


def _create_dir(path: str):
    if ospath.isfile(path):
        os.remove(path)
    if not ospath.exists(path):
        os.mkdir(path)


_create_dir(root_dir)


def GetNameList(path: str) -> list:
    root, this = ospath.split(path.rstrip(sep))
    names = [this] if this else []
    while root:
        root, this = ospath.split(root.rstrip(sep))
        if this: names.append(this)
    return names[::-1]


def _convert_path(path: str) -> str:
    return root_dir + path if path[0] == sep else root_dir + sep + path


def Create(path: str) -> str:
    path = _convert_path(path)
    names = GetNameList(path)
    path = ''
    for name in names:
        path += name + sep
        _create_dir(path)
    return path


def CreateFile(path: str):
    path = Create(path)
    if os.listdir(path):
        shutil.rmtree(path, ignore_errors=True)
        os.mkdir(path)
    return path


def Flush():
    shutil.rmtree(root_dir, ignore_errors=True)
    os.mkdir(root_dir)
