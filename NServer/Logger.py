from datetime import datetime

LogFile = 'log.txt'


# open(LogFile, 'w', encoding='utf-8')


def add(info: str):
    with open(LogFile, 'a', encoding='utf-8') as f:
        f.write(str(datetime.now()) + ' -> ' + info + '\n')
    # print(str(datetime.now()) + '> ' + info)


def addHost(ip: str, port: int, info: str):
    add(ip + ':%d ' % port + info)
