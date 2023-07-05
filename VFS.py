class Node:
    def __init__(self, name: str, isDir: bool, root=None):
        self.name = name
        if root is None:
            self.path = name
            root = self
        elif root is Root:
            self.path = root.path + name
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

    def isEmpty(self) -> bool:
        return self.isFile() or len(self.entities) <= 2

    def add(self, name: str, isDir: bool) -> bool:
        if self.isFile():
            return False
        if name in self.entities:
            return False
        self.entities[name] = Node(name, isDir, self)
        return True

    def remove(self, name: str) -> bool:
        if self.isFile() or name == '.' or name == '..':
            return False
        if name in self.entities:
            del self.entities[name]
            return True
        return False

    def __getitem__(self, item: str):
        return self.entities[item]

    def __contains__(self, item: str) -> bool:
        return self.isDir() and item in self.entities


def format():
    global Root
    Root = Node(Separator, True)


def init(paths: list, types: list):
    for path, typ in zip(paths, types):
        add(path, typ)


Separator = '/'
format()
CWD = Root
BadChars = '\\', '//', ':', '*', '?', '"', '<', '>', '|'


def check(path: str) -> bool:
    for c in BadChars:
        if c in path:
            return False
    return True


def isroot(path: str) -> bool:
    return path == Root.path


def parsePath(path: str) -> tuple:
    if isroot(path):
        cwd = Root
        path = '.'
    elif path[0] == Separator:
        cwd = Root
    else:
        cwd = CWD
    path = path.strip(Separator)
    nodes = path.split(Separator)
    last = nodes[len(nodes) - 1]
    return cwd, nodes, last


def cwdPath() -> str:
    return CWD.path


def nodeat(path: str) -> Node:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name in cwd:
            cwd = cwd[name]
        else:
            return None
    return cwd


def isempty(path: str) -> bool:
    node = nodeat(path)
    if node:
        return node.isEmpty()
    return True


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


def absPath(path: str) -> str:
    node = nodeat(path)
    if node:
        nodes = []
        while node != node['..']:
            nodes.append(node.name)
            node = node['..']
        return Root.path + Separator.join(nodes[::-1])
    return Root.path


def isparent(path: str) -> bool:
    return cwdPath().startswith(absPath(path))


def add(path: str, isDir: bool) -> bool:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name is last:
            return cwd.add(name, isDir)
        else:
            cwd.add(name, True)
        cwd = cwd[name]
    return False


def remove(path: str) -> bool:
    cwd, nodes, last = parsePath(path)
    for name in nodes:
        if name is last:
            return cwd.remove(name)
        if not (name in cwd):
            return False
        cwd = cwd[name]
    return False


def cd(path: str) -> bool:
    node = nodeat(path)
    if node and node.isDir():
        global CWD
        CWD = node
        return True
    return False


def ls(path) -> tuple:
    node = nodeat(path)
    if node:
        entities = node.entities
        if entities:
            names = []
            types = []
            for name in entities:
                if name != '.' and name != '..':
                    names.append(name)
                    types.append(entities[name].isFile())
            return names, types
    return None
