import logging
import subprocess
import os
from pathlib import Path

WG_PATH = Path(os.getcwd()) / "vendored/wg"
log = logging.getLogger(__name__)

class Interface:

    def connect(self, interface_name):
        pass

    def disconnect(self, interface_name):
        pass

    def _get_wg_status(self):
        if Path('/usr/bin/sudo').exists():
            serve_pwd = self.serve_sudo_pwd()
            p = subprocess.Popen(['/usr/bin/sudo', '-S', str(WG_PATH), 'show', 'all', 'dump'],
                                 stdin=serve_pwd.stdout,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 )
            p.wait()
            if p.returncode != 0:
                print('Failed to run `wg show all dump`:')
                print(p.stdout.read().decode().strip())
                print(p.stderr.read().decode().strip())
                return []
            lines = p.stdout.read().decode().strip().splitlines()
            return lines
        return '''
    wg0	qJ1YWXV6nPmouAditrRahp+5X/DlBJD02ZPkFjbLdE4=	iSOYKa61gszRvGnA4+IMkxEp364e1LrIcGuXcM4IeU8=	0	off
    wg0	YLA3Gq/GW0QrQQfPA5wq7zfXnQI94a7oA8780hwHxWU=	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	1630599999	0	0	off
    wg0	YLA3Gq/GW0QrQQfPA5wq7zfXnQI94a7oA8780hwHxWU=	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	0	0	0	off
    wg1	my_privkey	my_pubkey	0	off
    wg1	peer_pubkey	(none)	143.178.241.68:1194	10.88.88.1/32,192.168.2.0/24	0	0	0	off
    '''.strip().splitlines()

    def current_status_by_interface(self):
        last_interface = None
        data = self._get_wg_status()
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
                             'up': int(latest_handshake) > 0,
                             }
                if not interface_status.get('peers'):
                    interface_status['peers'] = []
                interface_status['peers'].append(peer_data)
                interface_status['peers'] = sorted(interface_status['peers'], key=lambda x: not x['up'])
            else:
                raise ValueError("Can't parse line %s, it has %s parts", line, len(parts))

        if last_interface:
            status_by_interface[last_interface] = interface_status
        return status_by_interface
