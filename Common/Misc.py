def num2order(i: int) -> str:
    if i % 10 == 1:
        return f'%dst' % i
    if i % 10 == 2:
        return f'%dnd' % i
    if i % 10 == 3:
        return f'%drd' % i
    return f'%dth' % i


class Enum:
    def __init__(self, start: int = -1):
        self.count = start

    def new(self, skip: int = 0):
        self.count += 1 + skip
        return self.count
