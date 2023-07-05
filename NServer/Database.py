from Common.Misc import num2order


class Table:
    def __init__(self, cols: tuple, types: tuple):
        self.size = len(cols)
        if self.size <= 0:
            raise ValueError('The numbers of columns must be positive')
        self.table = []
        if self.size != len(types):
            raise ValueError('The numbers of columns and their types mismatch')
        self.types = types
        self.name2id = {cols[i]: i for i in range(self.size)}

    def addRow(self, row: list) -> bool:
        l = len(row)
        if l != self.size:
            print('The number of columns in a row must be %d, bad row: ' % self.size + str(row))
            return False
        # Check the type of arguments
        for i in range(l):
            try:
                row[i] = self.types[i](row[i])
            except ValueError:
                print('Type of the %s value must be %s' % (num2order(i + 1), self.types[i].__name__))
                return False
        # Add row
        self.table.append(row)
        return True

    def __iter__(self) -> iter:
        return iter(self.table)


Servers = Table(('id', 'ip', 'status'), (int, str, int))
Objects = Table(('id', 'path', 'isDir'), (int, str, bool))
Chunks = Table(('fileId', 'no', 'serverId'), (int, str))


def GetSServerIPs() -> list:
    ips = []
    for row in Servers:
        ips.append(row[1])
    return ips


def GetPathsAndTypes() -> tuple:
    paths = []
    types = []
    for row in Objects:
        paths.append(row[1])
        types.append(row[2])
    return paths, types
