import functools
from threading import Event, RLock

from Common.Misc import Enum
from Common.Socket import socket

JobTypes = Enum(-1)
JT_Upload = JobTypes()
JT_Download = JobTypes()
JT_Replicate = JobTypes()

_jobs = [{}, {}, {}]

_locker = RLock()


def _lock(func):
    @functools.wraps(func)
    def wrapper(*args):
        with _locker:
            return func(*args)

    return wrapper


class Job:
    def __init__(self, job: int, path: str, typ: int):
        self.typ = typ
        self.id = job
        self.event = Event()
        self.path = path
        self.started = None
        _jobs[typ][job] = self

    def set(self, sock: socket):
        self.event.set()
        self.started = sock

    def wait(self, timeout: float = None) -> bool:
        return self.event.wait(timeout)

    def clear(self):
        self.event.clear()


@_lock
def AddUploadJob(job: int, path: str) -> Job:
    return Job(job, path, JT_Upload)


@_lock
def AddDownloadJob(job: int, path: str) -> Job:
    return Job(job, path, JT_Download)


@_lock
def AddReplicationJob(job: int, path: str) -> Job:
    return Job(job, path, JT_Replicate)


@_lock
def StartJob(sock: socket, job: int) -> Job:
    for typ in JobTypes:
        if job in _jobs[typ]:
            j: Job = _jobs[typ][job]
            j.set(sock)
            return j


@_lock
def CompleteJob(job: int):
    for i in JobTypes:
        if job in _jobs[i]:
            del _jobs[i][job]


@_lock
def AbortJob(sock: socket):
    for i in JobTypes:
        aborted = []
        for id, job in _jobs[i].items():
            if job.started is sock:
                aborted.append(id)
        for id in aborted:
            del _jobs[i][id]
