#!/usr/bin/env python3

"""stop.py — gracefully shut down bench Redis instances and free bound ports.

Reads the port suffix from ./config/redis_cache.conf, then for each known
bench port prefix (1100, 1200, 1300, 900, 800, 500) sends a Redis SHUTDOWN
via redis-cli.  Falls back to fuser -k for any port that remains in use.

Must be run from the bench directory (e.g. ~/frappe-bench).
"""

import os
import socket
import errno
import time

PORTS = [1100, 1200, 1300, 900, 800, 500]


def get_port_suffix():
    """Extract the last digit of the 'port' line from redis_cache.conf."""
    try:
        with open("./config/redis_cache.conf") as f:
            for line in f:
                key, _, value = line.partition(" ")
                if key.strip() == "port":
                    return value.strip()[-1:]
    except IOError:
        print("redis_cache.conf not found — are you in the bench directory?")
        raise SystemExit(1)
    print("No 'port' line found in redis_cache.conf")
    raise SystemExit(1)


def stop_port(port):
    """Attempt to free a single port: Redis SHUTDOWN first, then fuser -k."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        print(f"Port {port} already closed")
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            os.system(f"echo 'shutdown' | redis-cli -h 127.0.0.1 -p {port}")
            time.sleep(3)
            try:
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.bind(("127.0.0.1", port))
                sock2.close()
            except socket.error:
                os.system(f"fuser {port}/tcp -k")
    finally:
        sock.close()


def main():
    suffix = get_port_suffix()
    for prefix in PORTS:
        stop_port(int(f"{prefix}{suffix}"))
    print("bench stopped")


if __name__ == "__main__":
    main()
