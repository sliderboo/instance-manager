import socket
from redis import Redis
from config import config

min_port = config["DOCKER"]["MIN_PORT"]
max_port = config["DOCKER"]["MAX_PORT"]


def get_valid_port(locker: Redis, start_port: int = None):
    global max_port
    global min_port
    port = start_port or min_port
    port_limit = max_port
    for port in range(port, port_limit):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", port))
            sock.close()
            if not locker.get(f"port:{port}"):
                locker.set(f"port:{port}", 1)
                return port
        except:
            pass
    raise IOError("no free ports")
