from datetime import datetime

LogFile = 'log.txt'
# with open(LogFile, 'w', encoding='utf-8'):
#     pass


def add(info: str):
    # with open(LogFile, 'a', encoding='utf-8') as f:
    #     f.write(str(datetime.now()) + '> ' + info)
    print(str(datetime.now()) + '> ' + info)
