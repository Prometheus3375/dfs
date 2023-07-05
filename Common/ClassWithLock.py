import functools
from threading import RLock


def GetNOPubPM(cls, parent) -> dict:
    """
    Returns all public methods from parent which are not overwritten in class
    """
    return {
        k: v for k, v in vars(parent).items()
        if k not in vars(cls) and k[0] != '_' and callable(v)
    }


def _add_lock(func):
    @functools.wraps(func)
    def wrapper(self, *args):
        with self.lock:
            return func(self, *args)

    return wrapper


def CreateClassWithLock(parent, child):
    """
    Creates a class inherited from parent which acquires a lock before calling every public bound method.
    Parent class must not have attributes and static methods.
    Child is used to redefine __doc__ and etc in returning class
    """

    class ClassWithLock(parent):
        def __init__(self, *args):
            super().__init__(*args)
            self.lock = RLock()

    # Add vars of child to ClassWithLock and update vars of ClassWithLock
    for k, v in vars(child).items():
        setattr(ClassWithLock, k, v)
    # Update values that are not in vars
    ClassWithLock.__name__ = child.__name__
    ClassWithLock.__qualname__ = child.__qualname__
    if hasattr(child, '__annotations__'):
        ClassWithLock.__annotations__ = child.__annotations__
    # Overwrite non-overwritten public methods of parent
    for k, v in GetNOPubPM(ClassWithLock, parent).items():
        setattr(ClassWithLock, k, _add_lock(v))
    return ClassWithLock
