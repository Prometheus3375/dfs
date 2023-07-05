class Node:
    def __init__(self, name: str, isDir: bool, root=None):
        self.name = name
        if root is None:
            self.path = name
            root = self
        else:
            self.path = root.path + Separator + name
        if isDir:
            self.entities = {'.': self, '..': root}
        else:
            self.entities = None

    def isFile(self) -> bool:
        return self.entities is None

    def isDir(self) -> bool:
        return not self.isFile()

    def add(self, name: str, isDir: bool) -> bool:
        if self.isFile():
            return False
        if name in self.entities:
            return False
        self.entities[name] = Node(name, isDir, self)
        return True

    def remove(self, name: str) -> bool:
        if self.isFile():
            return False
        if name in self.entities:
            del self.entities[name]
            return True
        return False

    def __getitem__(self, item: str):
        return self.entities[item]

    def __contains__(self, item: str) -> bool:
        return item in self.entities

    def ls(self) -> list:
        if self.isFile():
            return None
        return self.entities.values()


Separator = '/'
Root = Node('~', True)
RootStart = Root.name + Separator
CWD = Root


def init(paths: list, types: list):
    for path, typ in zip(paths, types):
        add(path, typ)


def parsePath(path: str) -> tuple:
    if path.startswith(RootStart):
        cwd = Root
    else:
        cwd = CWD
    nodes = path.split(Separator)
    last = nodes[len(nodes) - 1]
    return cwd, nodes, last


def nodeat(path: str) -> Node:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name in cwd:
            cwd = cwd[name]
        else:
            return None
    return cwd


def isfile(path: str) -> bool:
    node = nodeat(path)
    if node:
        return node.isFile()
    return False


def isdir(path: str) -> bool:
    node = nodeat(path)
    if node:
        return node.isDir()
    return False


def exists(path: str) -> bool:
    node = nodeat(path)
    if node:
        return True
    return False


def add(path: str, isDir: bool) -> bool:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name is last:
            return cwd.add(name, isDir)
        else:
            cwd.add(name, True)
        cwd = cwd[name]


def remove(path: str) -> bool:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name is last:
            return cwd.remove(name)
        if not (name in cwd):
            return False
        cwd = cwd[name]


def cd(path: str) -> bool:
    node = nodeat(path)
    if node and node.isDir():
        global CWD
        CWD = node
        return True
    return False


def ls(path: str = '.') -> list:
    node = nodeat(path)
    if node:
        return node.ls()
    return None


def cwd_name() -> str:
    return CWD.path
