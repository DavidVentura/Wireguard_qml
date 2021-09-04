import struct
import socket
import subprocess
import time

import profile

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
    _connect()
    route = get_preferred_def_route()
    while True:
        new_route = get_preferred_def_route()
        if route == new_route:
            time.sleep(1)
            continue
        new_route = route
        _connect()

def _connect(profile_name):
    INTERFACE = 'wg0'
    profile = get_profile(profile_name)
    disconnect()

    # TODO: run on a loop based on network changes
    # TODO: try to create via `ip` and validate if the kernel module is there
    #with (LOG_DIR / 'out.log').open('w') as stdout, (LOG_DIR / 'err.log').open('w') as stderr:
    try:
        subprocess.check(['sudo', 'ip', 'link', 'add', 'wg0', 'type', 'wireguard'])
    except subprocess.CalledProcessError as e:
        print("Failed to use kernel module.. falling back to userspace implementation", flush=True)
        p = subprocess.Popen(['/usr/bin/sudo', '-E', 'vendored/wireguard', 'wg0',
        ],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL,
                           env={'WG_I_PREFER_BUGGY_USERSPACE_TO_POLISHED_KMOD': '1',
                                'WG_SUDO': '1',
                                'WG_LOG_LEVEL': 'trace', # boringtun
                                'WG_LOG_FILE': str(LOG_DIR / 'boring.log'),
                                'LOG_LEVEL': 'debug', # WG-go
                                },
                           start_new_session=True,
                           # to prevent being killed
                           )

        p.wait()

        if p.returncode != 0:
            print("Dying", flush=True)
            return err

    PROFILE_DIR = PROFILES_DIR / profile_name
    CONFIG_FILE = PROFILE_DIR / 'config.ini'

    p = subprocess.Popen(['/usr/bin/sudo', 'vendored/wg',
                          'setconf', INTERFACE, str(CONFIG_FILE)],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          )
    p.wait()
    err = p.stderr.read().decode()
    print(err, flush=True)
    print(p.stdout.read().decode(), flush=True)
    print(p.returncode, flush=True)
    if p.returncode != 0:
        return err

    # TODO: check return codes
    subprocess.run(['/usr/bin/sudo', 'ip', 'address', 'add', 'dev', INTERFACE, profile['ip_address']], check=True)
    subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'set', 'up', 'dev', INTERFACE], check=True)

    for extra_route in profile['extra_routes'].split(','):
        extra_route = extra_route.strip()
        subprocess.run(['/usr/bin/sudo', 'ip', 'route', 'add', extra_route, 'dev', INTERFACE], check=True)
