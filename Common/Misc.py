def num2order(i: int) -> str:
    if 10 > i > 20:
        if i % 10 == 1:
            return f'%dst' % i
        if i % 10 == 2:
            return f'%dnd' % i
        if i % 10 == 3:
            return f'%drd' % i
    return f'%dth' % i


class Enum:
    def __init__(self, start: int = -1):
        self.start = start
        self.top = start

    def new(self) -> int:
        self.top += 1
        return self.top

    def valid(self, i: int) -> bool:
        return self.start < i <= self.top


class MyException(Exception):
    def __init__(self, mes: str = ''):
        if mes:
            super(MyException, self).__init__(mes)
        else:
            super(MyException, self).__init__()
        self.message = mes

    def __str__(self):
        if self.message:
            return self.message
        return super(MyException, self).__str__()
