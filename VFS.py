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
        return item in self.entities


Separator = '/'
Root = Node('~', True)
RootStart = Root.name + Separator
RootStartLen = len(RootStart)
CWD = Root
BadChars = '\\', '//', ':', '*', '?', '"', '<', '>', '|'


def init(paths: list, types: list):
    for path, typ in zip(paths, types):
        add(path, typ)


def format():
    global Root
    Root = Node('~', True)


def check(path: str) -> bool:
    for c in BadChars:
        if c in path:
            return False
    return True


def parsePath(path: str) -> tuple:
    path = path.strip(Separator)
    if path == Root.path:
        cwd = Root
        path = '.'
    elif path.startswith(RootStart):
        cwd = Root
        path = path[RootStartLen:]
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


def cwdPath() -> str:
    return CWD.path


def absPath(path: str) -> str:
    cwd, nodes, last = parsePath(path)
    if cwd is Root:
        return '~'
    return cwd.path + Separator + Separator.join(nodes)
