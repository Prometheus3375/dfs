import os.path as ospath

from Common.Socket import CheckIP, CheckNet


def GetIPOrDomain(path: str, prompt: str) -> str:
    ip = ''
    # Read ip
    if ospath.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            ip = f.read().strip()
        ip = CheckIP(ip)
    # If read IP is invalid, ask it
    if not ip:
        prompt += ': '
        while True:
            ip = input(prompt).strip()
            # Check IP or domain
            ip = CheckIP(ip)
            if ip: break
            print('Error: \'%s\' - no such IP or domain' % ip)
    # Save IP
    with open(path, 'w', encoding='utf-8') as f:
        f.write(ip + '\n')
    return ip


def GetNet(path: str, prompt: str) -> str:
    net = ''
    if ospath.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            net = f.read().strip()
        if CheckNet(net):
            net = ''
    # If read net is invalid, ask it
    if not net:
        prompt += ': '
        while True:
            net = input(prompt).strip()
            # Check net
            res = CheckNet(net)
            if not res:
                break
            print(res)
    # Save net
    with open(path, 'w', encoding='utf-8') as f:
        f.write(net + '\n')
    return net
