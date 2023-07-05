from threading import Lock

_jobs = set()

_lock = Lock()


def new() -> int:
    with _lock:
        m = max(_jobs) + 2  # so range(m) contains max(_jobs) and max(_jobs) + 1
        free = [i for i in range(m) if i not in _jobs]
        job = free[0]
        _jobs.add(job)
        return job


def complete(job: int):
    with _lock:
        _jobs.remove(job)
