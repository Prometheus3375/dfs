from threading import RLock

from Common import TEST
from Common.VFS import FileSystem

Actual = FileSystem()
Actual_BackUp = 'ActualFS.txt'
Actual_Lock = RLock()
Pending = FileSystem()
Pending_Lock = RLock()


def WalkActual() -> list:
    with Actual_Lock:
        return Actual.walkWithTypes()


def SaveActual():
    with open(Actual_BackUp, 'w', encoding='utf-8') as f:
        paths = WalkActual()
        f.write('\n'.join(paths) + '\n')


def LoadActual(skip_malformed: bool = True):
    with open(Actual_BackUp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with Actual_Lock:
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
