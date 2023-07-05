import functools
from threading import RLock

from Common.Socket import socket

_jobs = {}

_locker = RLock()


def _lock(func):
    @functools.wraps(func)
    def wrapper(*args):
        with _locker:
            return func(*args)

    return wrapper


@_lock
def new(sock: socket) -> int:
    m = max(_jobs) + 2 if _jobs else 0
    m += 2  # so range(m) contains max(_jobs) and max(_jobs) + 1
    free = [i for i in range(m) if i not in _jobs]
    job = free[0]
    _jobs[job] = sock
    return job


@_lock
def complete(job: int):
    del _jobs[job]


@_lock
def abort(sock: socket):
    aborted = []
    for job, s in _jobs.items():
        if s is sock:
            aborted.append(job)
    for job in aborted:
        del _jobs[job]
