import os

from Common.Constants import TEST
from Common.VFS import LockFS

Actual = LockFS()
Actual_BackUp = 'ActualFS.txt'


def SaveActual():
    with open(Actual_BackUp, 'w', encoding='utf-8') as f:
        paths = Actual.walkWithTypes()
        f.write('\n'.join(paths) + '\n')


def LoadActual(skip_malformed: bool = True):
    if os.path.exists(Actual_BackUp):
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
