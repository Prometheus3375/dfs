import os

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
