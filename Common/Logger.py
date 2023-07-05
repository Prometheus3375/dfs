import os
from datetime import datetime

from Common.ClassWithLock import CreateClassWithLock

LogDateFormat = '%Y-%m-%d %H:%M:%S.%f'
NameFormat = '_%Y-%m-%d_%H-%M-%S'


class Logger:
    def __init__(self, path: str, save_old: bool = True):
        self.file = path
        # Save old if necessary
        if save_old and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as old:
                p, ext = os.path.splitext(path)
                p = p + datetime.now().strftime(NameFormat) + ext
                with open(p, 'w', encoding='utf-8') as new:
                    new.write(old.read())
        # Clean logfile or create new
        with open(path, 'w', encoding='utf-8'): pass

    def add(self, info: str):
        with open(self.file, 'a', encoding='utf-8') as f:
            f.write(datetime.now().strftime(LogDateFormat) + ' -> ' + info + '\n')

    def addHost(self, ip: str, port: int, info: str):
        self.add(ip + ':%d ' % port + info)


class ServerLogger(Logger): pass


ServerLogger = CreateClassWithLock(Logger, ServerLogger)
