class VFSException(Exception):
    def __init__(self, mes: str):
        super().__init__()
        self.message = mes

    def __str__(self):
        return self.message


class Node:
    def __init__(self, name: str, isDir: bool, root):
        self.name = name
        self.isDir = isDir
        self.isFile = not isDir
        if root is None:
            root = self
        self.root = root

    @staticmethod
    def new(name: str, isDir: bool, root=None):
        if isDir:
            return Dir(name, root)
        return Node(name, False, root)

    def getPath(self) -> str:
        if self is Root:
            return self.name
        path = self.name
        node = self.root
        while not (node is Root):
            path = node.name + Separator + path
            node = node.root
        return Root.name + path

    def raiseIfFile(self):
        raise VFSException(f'\'%s\' is not a directory' % self.getPath())

    def isRoot(self):
        return self is Root

    def delete(self):
        if self is Root:
            raise VFSException('Root directory cannot be removed')
        self.root._remove(self)

    def rename(self, newname: str):
        if self is Root:
            raise VFSException('Root directory cannot be renamed')
        # Remove node from root
        self.root._remove(self)
        # Change name
        self.name = newname
        # Add node to new root
        self.root._add(self)

    def _canBeMoved(self, newroot):
        if self is Root:
            raise VFSException('Root directory cannot be moved')
        # Check if new root is not a file
        newroot.raiseIfFile()
        # Check if new root can contain this node
        if self.name in newroot:
            raise VFSException(f'\'%s\' already contains \'%s\'' % (newroot.getPath(), self.name))

    def _move(self, newroot):
        # Remove node from old root
        self.root._remove(self)
        # Add node to new root
        newroot._add(self)
        # Update root
        self.root = newroot

    def move(self, newroot):
        self._canBeMoved(newroot)
        self._move(newroot)

    def _canBeCopied(self, newroot):
        if self is Root:
            raise VFSException('Root directory cannot be copied')
        # Check if new root is not a file
        newroot.raiseIfFile()
        # Check if new root can contain this node
        if self.name in newroot:
            raise VFSException(f'\'%s\' already contains \'%s\'' % (newroot.getPath(), self.name))

    def _copy(self, newroot):
        return Node.new(self.name, self.isDir, newroot)

    def copy(self, newroot):
        self._canBeCopied(newroot)
        clone = self._copy(newroot)
        newroot._add(clone)
        return clone


class Dir(Node):
    def __init__(self, name: str, root):
        super().__init__(name, True, root)
        self.entities = {}

    def raiseIfFile(self):
        pass

    def __contains__(self, name: str) -> bool:
        return name == '.' or name == '..' or name in self.entities

    def __getitem__(self, name: str):
        if name == '.':
            return self
        if name == '..':
            return self.root
        return self.entities[name]

    def isEmpty(self) -> bool:
        return len(self.entities) == 0

    def allSubnodes(self) -> list:
        subs = list(self.entities.values())
        for i in range(len(subs)):
            if subs[i].isDir:
                subs += subs[i].allSubnodes()
        return subs

    def allSubdirs(self) -> list:
        subs = [d for d in self.entities.values() if d.isDir]
        for i in range(len(subs)):
            subs += subs[i].allSubdirs()
        return subs

    def hasInSubnodes(self, node):
        return node in self.allSubnodes()

    def hasInSubdirs(self, node):
        return node in self.allSubdirs()

    def isCWDParent(self):
        return self is CWD or CWD in self.allSubdirs()

    def _add(self, node: Node):
        self.entities[node.name] = node

    def _remove(self, node: Node):
        del self.entities[node.name]

    def _canBeMoved(self, newroot):
        Node._canBeMoved(self, newroot)
        # Check if new root is not self
        if newroot is self:
            raise VFSException(f'\'%s\' cannot be moved to itself' % self.getPath())
        # Check if new root is not a subdirectory
        if newroot in self.allSubdirs():
            raise VFSException(
                f'\'%s\' cannot be moved to its subdirectory \'%s\'' % (self.getPath(), newroot.getPath())
            )

    def copy(self, newroot):
        self._canBeCopied(newroot)
        clone = self._copy(newroot)
        for node in self.entities.values():
            node.copy(clone)
        newroot._add(clone)
        return clone

    def add(self, name: str, isDir: bool):
        if name in self:
            raise VFSException(f'\'%s\' already contains \'%s\'' % (self.getPath(), name))
        new = Node.new(name, isDir, self)
        self._add(new)
        return new

    def walk(self) -> list:
        return self.allSubnodes()


def format():
    global Root, CWD, RootPath, CWDPath
    Root = Node.new(Separator, True)
    CWD = Root
    RootPath = Root.getPath()
    CWDPath = RootPath


def init(paths: list, types: list):
    for path, typ in zip(paths, types):
        add(path, typ)


Separator = '/'
format()
_bad_chars = '\\', ':', '*', '?', '"', '<', '>', '|', '\t'
BadPathChars = Separator * 2, *_bad_chars
BadNameChars = Separator, *_bad_chars


def raiseIfBadPath(path: str):
    for c in BadPathChars:
        if c in path:
            raise VFSException(f'\'%s\' is not a valid path. Path must not contain next character sequences: \'%s\''
                               % (path, '\', \''.join(BadPathChars)))


def raiseIfBadName(name: str):
    if name == '.' or name == '..':
        raise VFSException(f'\'%s\' is not a valid name. Names \'.\' and \'..\' are reserved by the system' % name)
    for c in BadNameChars:
        if c in name:
            raise VFSException(f'\'%s\' is not a valid name. Name must not contain next character sequences: \'%s\''
                               % (name, '\', \''.join(BadNameChars)))


def parsePath(path: str) -> tuple:
    raiseIfBadPath(path)
    if path == RootPath:
        cwd = Root
        path = '.'
    elif path[0] == Separator:
        cwd = Root
    else:
        cwd = CWD
    path = path.lower().strip(Separator)
    nodes = path.split(Separator)
    return cwd, nodes


def cwdPath() -> str:
    return CWDPath


def _nodeat(path: str) -> Node:
    cwd, nodes = parsePath(path)
    for name in nodes:
        if cwd.isDir and name in cwd:
            cwd = cwd[name]
        else:
            return None
    return cwd


def nodeat(path: str) -> Node:
    node = _nodeat(path)
    if node:
        return node
    raise VFSException(f'\'%s\' does not exist' % path)


def dirat(path: str) -> Dir:
    node = nodeat(path)
    node.raiseIfFile()
    return node


def isabs(path: str) -> bool:
    if path == RootPath:
        return True
    cwd, nodes = parsePath(path)
    if any([name == '.' or name == '..' for name in nodes]):
        return False
    return cwd is Root


def absPath(path: str) -> str:
    return nodeat(path).getPath()


def isparent(path: str) -> bool:
    return dirat(path).isCWDParent()


def isroot(path: str) -> bool:
    return _nodeat(path) is Root


def isempty(path: str) -> bool:
    node = _nodeat(path)
    if node and node.isDir:
        return node.isEmpty()
    return True


def isfile(path: str) -> bool:
    node = _nodeat(path)
    if node:
        return node.isFile
    return False


def isdir(path: str) -> bool:
    node = _nodeat(path)
    if node:
        return node.isDir
    return False


def exists(path: str) -> bool:
    node = _nodeat(path)
    if node:
        return True
    return False


def add(path: str, isDir: bool):
    cwd, nodes = parsePath(path)
    last = len(nodes) - 1
    lastname = nodes[last]
    raiseIfBadName(lastname)
    # >>> first, last = '1/1'.split(/)
    # >>> first is last
    # True
    # >>> first, last = 'some/some'.split(/)
    # >>> first is last
    # False
    # It is not possible to use (a is b) check here
    for i in range(last):
        name = nodes[i]
        if not (name in cwd):
            cwd.add(name, True)
        cwd = cwd[name]
        cwd.raiseIfFile()
    cwd.add(lastname, isDir)


def remove(path: str):
    nodeat(path).delete()


def rename(what: str, name: str):
    node = nodeat(what)
    raiseIfBadName(name)
    node.rename(name)


def dirat_cin(path: str) -> Dir:
    # cin = create if necessary
    cwd, nodes = parsePath(path)
    for name in nodes:
        if not (name in cwd):
            cwd.add(name, True)
        cwd = cwd[name]
        cwd.raiseIfFile()
    return cwd


def moveNode(node: Node, to: str):
    newroot = dirat_cin(to)
    node.move(newroot)


def move(what: str, to: str):
    moveNode(nodeat(what), to)


def copy(what: str, to: str):
    node = nodeat(what)
    newroot = dirat_cin(to)
    node.copy(newroot)


def cd(path: str):
    node = nodeat(path)
    node.raiseIfFile()
    global CWD, CWDPath
    CWD = node
    CWDPath = CWD.getPath()


def ls(path) -> tuple:
    node = dirat(path)
    entities = node.entities.values()
    names = []
    types = []
    for node in entities:
        names.append(node.name)
        types.append(node.isFile)
    return names, types


def walk() -> list:
    return [node.getPath() for node in CWD.walk()]
