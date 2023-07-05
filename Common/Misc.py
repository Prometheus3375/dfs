def num2order(i: int) -> str:
    if 10 > i > 20:
        if i % 10 == 1:
            return '%dst' % i
        if i % 10 == 2:
            return '%dnd' % i
        if i % 10 == 3:
            return '%drd' % i
    return '%dth' % i


class Enum:
    def __init__(self, start: int = -1):
        self.start = start
        self.top = start

    def __call__(self) -> int:
        self.top += 1
        return self.top

    def __contains__(self, i: int) -> bool:
        return self.start < i <= self.top


class EnumCode:
    def __init__(self):
        self.codes = []
        self.top = -1

    def __call__(self, message: str) -> int:
        self.top += 1
        self.codes.append(message)
        return self.top

    def __contains__(self, i: int) -> bool:
        return -1 - self.top <= i <= self.top

    def __getitem__(self, i: int) -> str:
        return self.codes[i]


class MyException(Exception):
    def __init__(self, msg: str = ''):
        if msg:
            super().__init__(msg)
            self.message = msg
        else:
            super().__init__()
            self.message = super().__str__()

    def __str__(self) -> str:
        return self.message


class MyError(MyException):
    def __init__(self, errors: EnumCode, err_code: int, msg: str = ''):
        super().__init__(msg)
        self.code = err_code
        if not msg and err_code in errors:
            self.message = errors[err_code]
