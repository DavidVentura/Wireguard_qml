import struct
import socket
import subprocess
import time

import interface

def get_preferred_def_route():
    metric = 999999999
    ip = None
    for line in open('/proc/net/route').readlines():
        line = line.split()
        if line[1] != '00000000' or not int(line[3], 16) & 2:
            # If not default route or not RTF_GATEWAY, skip it
            continue

        if int(line[6]) > metric:
            continue
        ip = socket.inet_ntoa(struct.pack("<L", int(line[2], 16)))
    return ip


def keep_tunnel():
    # FIXME what if it has to go down
    interface.connect()
    route = get_preferred_def_route()
    while True:
        new_route = get_preferred_def_route()
        if route == new_route:
            time.sleep(1)
            continue
        new_route = route
        interface._connect()
