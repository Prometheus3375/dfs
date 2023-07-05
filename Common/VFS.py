from Common.ClassWithLock import CreateClassWithLock
from Common.Misc import MyException

Separator = '/'
RootName = Separator
_bad_chars = '\\', ':', '*', '?', '"', '<', '>', '|', '\t'
BadPathChars = Separator * 2, *_bad_chars
BadNameChars = Separator, *_bad_chars
Walk_PathTypeSep = '\t'


def IsBadPath(path: str) -> bool:
    for c in BadPathChars:
        if c in path:
            return True
    return False


def IsBadName(name: str) -> bool:
    if name == '.' or name == '..':
        return True
    for c in BadNameChars:
        if c in name:
            return True
    return False


def RaiseIfBadPath(path: str):
    if IsBadPath(path):
        raise VFSException('\'%s\' is not a valid path. Path must not contain next character sequences: \'%s\''
                           % (path, '\', \''.join(BadPathChars)))


def RaiseIfBadName(name: str):
    if name == '.' or name == '..':
        raise VFSException('\'%s\' is not a valid name. Names \'.\' and \'..\' are reserved by the system' % name)
    if IsBadName(name):
        raise VFSException('\'%s\' is not a valid name. Name must not contain next character sequences: \'%s\''
                           % (name, '\', \''.join(BadNameChars)))


class VFSException(MyException):
    pass


class Node:
    def __init__(self, name: str, parent):
        self.name = name
        self.parent = parent
        self.isDir = isinstance(self, Dir)
        self.isFile = not self.isDir
        self.isRoot = isinstance(self, RootDir)

    @staticmethod
    def new(name: str, parent, isDir: bool):
        if isDir:
            return Dir(name, parent)
        return Node(name, parent)

    def getPath(self) -> str:
        path = self.name
        node = self.parent
        while not node.isRoot:
            path = node.name + Separator + path
            node = node.parent
        return RootName + path

    def raiseIfFile(self):
        raise VFSException('\'%s\' is not a directory' % self.getPath())

    def delete(self):
        self.parent._remove(self)

    def rename(self, newname: str):
        RaiseIfBadName(newname)
        if newname in self.parent:
            raise VFSException('\'%s\' already contains \'%s\'' % (self.parent.getPath(), newname))
        # Remove node from parent
        self.parent._remove(self)
        # Change name
        self.name = newname
        # Add node to new parent
        self.parent._add(self)

    def canBeMoved(self, newparent):
        # Check if new parent is not a file
        newparent.raiseIfFile()
        # Check if new parent can contain this node
        if self.name in newparent:
            raise VFSException('\'%s\' already contains \'%s\'' % (newparent.getPath(), self.name))

    def _move(self, newparent):
        # Remove node from old parent
        self.parent._remove(self)
        # Add node to new parent
        newparent._add(self)
        # Update parent
        self.parent = newparent

    def move(self, newparent):
        self.canBeMoved(newparent)
        self._move(newparent)

    def canBeCopied(self, newparent):
        # Check if new parent is not a file
        newparent.raiseIfFile()
        # Check if new parent can contain this node
        if self.name in newparent:
            raise VFSException('\'%s\' already contains \'%s\'' % (newparent.getPath(), self.name))

    def _copy(self, newparent):
        # Create a clone
        clone = Node.new(self.name, newparent, self.isDir)
        # Add to new parent
        newparent._add(clone)
        # Return clone
        return clone

    def copy(self, newparent):
        self.canBeCopied(newparent)
        return self._copy(newparent)


class Dir(Node):
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.entities = {}

    def raiseIfFile(self):
        pass

    def __contains__(self, name: str) -> bool:
        return name == '.' or name == '..' or name in self.entities

    def __getitem__(self, name: str):
        if name == '.':
            return self
        if name == '..':
            return self.parent
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

    def _add(self, node: Node):
        self.entities[node.name] = node

    def _remove(self, node: Node):
        del self.entities[node.name]

    def canBeMoved(self, newparent):
        Node.canBeMoved(self, newparent)
        # Check if new parent is not self
        if newparent is self:
            raise VFSException('\'%s\' cannot be moved to itself' % self.getPath())
        # Check if new parent is not a subdirectory
        if newparent in self.allSubdirs():
            raise VFSException(
                '\'%s\' cannot be moved to its subdirectory \'%s\'' % (self.getPath(), newparent.getPath())
            )

    def _copy(self, newparent):
        # Create a clone
        clone = Node.new(self.name, newparent, self.isDir)
        # Add copies of subnodes to clone
        for node in self.entities.values():
            node._copy(clone)
        # Add to new parent
        newparent._add(clone)
        # Return clone
        return clone

    def add(self, name: str, isDir: bool) -> Node:
        if name in self:
            raise VFSException('\'%s\' already contains \'%s\'' % (self.getPath(), name))
        new = Node.new(name, self, isDir)
        self._add(new)
        return new

    def walk(self) -> list:
        return self.allSubnodes()


class RootDir(Dir):
    def __init__(self):
        super().__init__(RootName, None)
        self.parent = self

    def getPath(self) -> str:
        return self.name

    def delete(self):
        raise VFSException('Root directory cannot be removed')

    def rename(self, newname: str):
        raise VFSException('Root directory cannot be renamed')

    def canBeMoved(self, newparent):
        raise VFSException('Root directory cannot be moved')

    def _move(self, newparent):
        pass

    def canBeCopied(self, newparent):
        raise VFSException('Root directory cannot be copied')

    def _copy(self, newparent):
        return self


class FileSystem:
    def __init__(self):
        self.Root = RootDir()
        self.RootPath = self.Root.getPath()
        self.CWD = self.Root
        self.CWDPath = self.RootPath

    def parsePath(self, path: str) -> tuple:
        RaiseIfBadPath(path)
        if path == self.RootPath:
            cwd = self.Root
            path = '.'
        elif path[0] == Separator:
            cwd = self.Root
        else:
            cwd = self.CWD
        path = path.lower().strip(Separator)
        nodes = path.split(Separator)
        return cwd, nodes

    def _nodeAt(self, path: str) -> Node:
        cwd, nodes = self.parsePath(path)
        for name in nodes:
            if cwd.isDir and name in cwd:
                cwd = cwd[name]
            else:
                # noinspection PyTypeChecker
                return None
        return cwd

    def nodeAt(self, path: str) -> Node:
        node = self._nodeAt(path)
        if node:
            return node
        raise VFSException('\'%s\' does not exist' % path)

    def dirAt(self, path: str) -> Dir:
        node = self.nodeAt(path)
        node.raiseIfFile()
        # noinspection PyTypeChecker
        return node

    def dirAtCN(self, path: str) -> Dir:
        # CN = create if necessary
        cwd, nodes = self.parsePath(path)
        for name in nodes:
            if name in cwd:
                cwd = cwd[name]
                cwd.raiseIfFile()
            else:
                cwd = cwd.add(name, True)
        return cwd

    def isAbs(self, path: str) -> bool:
        if path == self.RootPath:
            return True
        cwd, nodes = self.parsePath(path)
        if any([name == '.' or name == '..' for name in nodes]):
            return False
        return cwd is self.Root

    def absPath(self, path: str) -> str:
        return self.nodeAt(path).getPath()

    def isCWDAncestor(self, d: Dir) -> bool:
        return d is self.CWD or self.CWD in d.allSubdirs()

    def isRoot(self, path: str) -> bool:
        try:
            node = self._nodeAt(path)
        except VFSException:
            return False
        return node is self.Root

    def isEmpty(self, path: str) -> bool:
        try:
            node = self._nodeAt(path)
        except VFSException:
            return False
        if node and node.isDir:
            # noinspection PyUnresolvedReferences
            return node.isEmpty()
        return True

    def exists(self, path: str) -> bool:
        try:
            node = self._nodeAt(path)
        except VFSException:
            return False
        if node:
            return True
        return False

    def isFile(self, path: str) -> bool:
        try:
            node = self._nodeAt(path)
        except VFSException:
            return False
        if node:
            return node.isFile
        return False

    def isDir(self, path: str) -> bool:
        try:
            node = self._nodeAt(path)
        except VFSException:
            return False
        if node:
            return node.isDir
        return False

    def canBeAdded(self, path: str) -> bool:
        try:
            cwd, nodes = self.parsePath(path)
            last = len(nodes) - 1
            lastname = nodes[last]
            RaiseIfBadName(lastname)
            for i in range(last):
                name = nodes[i]
                if name in cwd:
                    cwd = cwd[name]
                    cwd.raiseIfFile()
                else:
                    # No node with such path -> can be added
                    return True
            return lastname not in cwd
        except VFSException:
            return False

    def cantBeAdded(self, path: str) -> bool:
        return not self.canBeAdded(path)

    def add(self, path: str, isDir: bool) -> Node:
        cwd, nodes = self.parsePath(path)
        last = len(nodes) - 1
        lastname = nodes[last]
        RaiseIfBadName(lastname)
        # >>> first, last = '1/1'.split(/)
        # >>> first is last
        # True
        # >>> first, last = 'some/some'.split(/)
        # >>> first is last
        # False
        # It is not possible to use (a is b) check here
        for i in range(last):
            name = nodes[i]
            if name in cwd:
                cwd = cwd[name]
                cwd.raiseIfFile()
            else:
                cwd = cwd.add(name, True)
        return cwd.add(lastname, isDir)

    def canBeRemoved(self, path: str) -> bool:
        try:
            node = self.nodeAt(path)
            return node is not self.Root
        except VFSException:
            return False

    def cantBeRemoved(self, path: str) -> bool:
        return not self.canBeRemoved(path)

    def remove(self, path: str) -> Node:
        node = self.nodeAt(path)
        node.delete()
        return node

    def canBeRenamed(self, what: str, name: str):
        try:
            RaiseIfBadName(name)
            node = self.nodeAt(what)
            return node is not self.Root and name.lower() not in node.parent
        except VFSException:
            return False

    def cantBeRenamed(self, what: str, name: str):
        return not self.canBeRenamed(what, name)

    def rename(self, what: str, name: str) -> Node:
        node = self.nodeAt(what)
        node.rename(name.lower())
        return node

    def canBeMoved(self, what: str, to: str) -> bool:
        try:
            node = self.nodeAt(what)
            newparent = self._nodeAt(to)
            if newparent:
                # noinspection PyTypeChecker
                node.canBeMoved(newparent)
            return True
        except VFSException:
            return False

    def cantBeMoved(self, what: str, to: str) -> bool:
        return not self.canBeMoved(what, to)

    def moveNode(self, node: Node, to: str):
        newparent = self.dirAtCN(to)
        node.move(newparent)

    def move(self, what: str, to: str) -> Node:
        node = self.nodeAt(what)
        self.moveNode(node, to)
        return node

    def canBeCopied(self, what: str, to: str) -> bool:
        try:
            node = self.nodeAt(what)
            newparent = self._nodeAt(to)
            if newparent:
                # noinspection PyTypeChecker
                node.canBeCopied(newparent)
            return True
        except VFSException:
            return False

    def cantBeCopied(self, what: str, to: str) -> bool:
        return not self.canBeCopied(what, to)

    def copyNode(self, node: Node, to: str) -> Node:
        newparent = self.dirAtCN(to)
        return node.copy(newparent)

    def copy(self, what: str, to: str) -> Node:
        return self.copyNode(self.nodeAt(what), to)

    def fill(self, paths_types: list):
        for pt in paths_types:
            path, isDir = pt
            if self.canBeAdded(path):
                self.add(path, isDir)

    def flush(self):
        FileSystem.__init__(self)

    def cd(self, path: str):
        node = self.dirAt(path)
        self.CWD = node
        self.CWDPath = node.getPath()

    def ls(self, path: str) -> tuple:
        node = self.dirAt(path)
        entities = node.entities.values()
        names = []
        types = []
        for node in entities:
            names.append(node.name)
            types.append(node.isFile)
        return names, types

    def walk(self) -> list:
        return [node.getPath() for node in self.Root.walk()]

    def walkWithTypes(self) -> list:
        return [node.getPath() + Walk_PathTypeSep + str(node.isDir) for node in self.Root.walk()]

    def fillFromLines(self, lines: list, skip_malformed: bool = True):
        check = not skip_malformed
        pts = []
        for line in lines:
            t = line.strip().split(Walk_PathTypeSep)
            if len(t) == 2:
                path, typ = t
                isDir = typ == 'True'
                if isDir or typ == 'False':
                    pts.append((path, isDir))
                elif check:
                    raise ValueError('Line \'%s\' has invalid node type' % line)
            elif check:
                raise ValueError('Line \'%s\' is malformed' % line)
        self.fill(pts)


class LockFS(FileSystem): pass


LockFS = CreateClassWithLock(FileSystem, LockFS)
