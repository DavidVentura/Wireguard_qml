import subprocess
from pathlib import Path
INTERFACE = 'wg0'

def _connect(profile, config_file):
    disconnect()

    # TODO: run on a loop based on network changes
    # TODO: try to create via `ip` and validate if the kernel module is there
    #with (LOG_DIR / 'out.log').open('w') as stdout, (LOG_DIR / 'err.log').open('w') as stderr:
    try:
        subprocess.run(['sudo', 'ip', 'link', 'add', 'wg0', 'type', 'wireguard'], check=True)
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

    p = subprocess.Popen(['/usr/bin/sudo', 'vendored/wg',
                          'setconf', INTERFACE, str(config_file)],
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

#

def disconnect():
    # It is fine to have this fail, it is only trying to cleanup before starting
    subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'del', 'dev', INTERFACE],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=False)
#

def _get_wg_status():
    if Path('/usr/bin/sudo').exists():
        return subprocess.check_output(['/usr/bin/sudo', 'vendored/wg', 'show', 'all', 'dump']).decode().strip().splitlines()
    return '''
wg0	qJ1YWXV6nPmouAditrRahp+5X/DlBJD02ZPkFjbLdE4=	iSOYKa61gszRvGnA4+IMkxEp364e1LrIcGuXcM4IeU8=	0	off
wg0	YLA3Gq/GW0QrQQfPA5wq7zfXnQI94a7oA8780hwHxWU=	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	0	0	0	off
wg0	YLA3Gq/GW0QrQQfPA5wq7zfXnQI94a7oA8780hwHxWU=	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	0	0	0	off
wg1	my_privkey	my_pubkey	0	off
wg1	peer_pubkey	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	0	0	0	off
'''.strip().splitlines()

def current_status_by_interface():
    last_interface = None
    data = _get_wg_status()
    interface_status = {}
    status_by_interface = {}
    peers = []
    for line in data:
        parts = line.split('\t')
        iface = parts[0]
        if iface != last_interface and interface_status:
            status_by_interface[last_interface] = interface_status
            interface_status = {}

        if len(parts) == 5:
            iface, private_key, public_key, listen_port, fwmark = parts
            interface_status['my_privkey'] = private_key
            interface_status['peers'] = []
            last_interface = iface
        elif len(parts) == 9:
            iface, public_key, preshared_key, endpoint, allowed_ips, latest_handshake, transfer_rx, transfer_tx, persistent_keepalive = parts
            peer_data = {'public_key': public_key,
                         'rx': transfer_rx,
                         'tx': transfer_tx,
                         'latest_handshake': latest_handshake,
                         }
            interface_status['peers'].append(peer_data)
        else:
            raise ValueError("Can't parse line %s, it has %s parts", line, len(parts))

    if last_interface:
        status_by_interface[last_interface] = interface_status
    return status_by_interface
