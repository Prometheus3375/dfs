import functools
from threading import RLock

from Common.Constants import TEST
from Common.Misc import GetPubPM
from Common.VFS import FileSystem


class FSWithLock(FileSystem):
    def __init__(self):
        super().__init__()
        self.lock = RLock()


def _add_lock(func):
    @functools.wraps(func)
    def wrapper(self, *args):
        with self.lock:
            return func(self, *args)

    return wrapper


# Override public FileSystem methods
for k, v in GetPubPM(FSWithLock, FileSystem).items():
    setattr(FSWithLock, k, _add_lock(v))
# Define file systems
Actual = FSWithLock()
Actual_BackUp = 'ActualFS.txt'
Pending = FSWithLock()


def SaveActual():
    with open(Actual_BackUp, 'w', encoding='utf-8') as f:
        paths = Actual.walkWithTypes()
        f.write('\n'.join(paths) + '\n')


def LoadActual(skip_malformed: bool = True):
    with open(Actual_BackUp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    Actual.fillFromLines(lines, skip_malformed)


if __name__ == '__main__':
    Actual.add('some/cool/path/file.txt', False)
    Actual.add('some/cool/kekw.txt', False)
    Actual.copy('some/cool', '/')
    print('Something added')
    print(*Actual.walkWithTypes(), sep='\n')
    SaveActual()
    Actual.flush()
    print('Flushed')
    print(*Actual.walkWithTypes(), sep='\n')
    LoadActual()
    print('Loaded')
    print(*Actual.walkWithTypes(), sep='\n')
elif TEST:
    Actual.add('some/cool/path/file.txt', False)
    Actual.add('some/cool/kekw.txt', False)
    Actual.copy('some/cool', '/')
    Pending.fillFromLines(Actual.walkWithTypes())
