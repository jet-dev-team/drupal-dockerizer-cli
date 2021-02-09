from contextlib import closing
import socket

def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(3)
        return sock.connect_ex((host, port)) == 0


def getNetworkId():
    ipRange = range(2, 256)
    network_id = 2
    for i in ipRange:
        network_id = i
        ip = f'192.168.{i}.10'
        if not check_socket(ip, 80):
            break
    return network_id


def checkLocalhostPort(port):
    location = not check_socket('127.0.0.1', port)
    if location:
        print(f'Port {port} is open\r\n')
    else:
        raise ConnectionError(
            f'Port {port} is not open. Please down app on this port or choose another port.')
