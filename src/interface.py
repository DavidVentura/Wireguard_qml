import logging
import subprocess
import os
from pathlib import Path

WG_PATH = Path(os.getcwd()) / "vendored/wg"
log = logging.getLogger(__name__)

class Interface:
    def __init__(self, sudo_pwd):
        # sudo_cmd_list variable is a list like: ['echo', 'password', '|', '/usr/bin/sudo', '-S']
        self._sudo_pwd = sudo_pwd

    def serve_sudo_pwd(self):
        return subprocess.Popen(['echo', self._sudo_pwd], stdout=subprocess.PIPE)

    def _connect(self, profile, config_file, use_kmod):
        interface_name = profile['interface_name']
        self.disconnect(interface_name)

        if use_kmod:
            serve_pwd = self.serve_sudo_pwd()
            subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'add', interface_name, 'type', 'wireguard'],
                            stdin=serve_pwd.stdout,
                            check=True)
            self.config_interface(profile, config_file)
        else:
            self.start_daemon(profile, config_file)


    def start_daemon(self, profile, config_file):
        serve_pwd = self.serve_sudo_pwd()
        p = subprocess.Popen(['/usr/bin/sudo', '-S', '/usr/bin/python3', 'src/daemon.py', profile['profile_name'], self._sudo_pwd],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              stdin=serve_pwd.stdout,
                              start_new_session=True,
                            )
        print('started daemon')

    def config_interface(self, profile, config_file):
        interface_name = profile['interface_name']
        log.info('Configuring interface %s', interface_name)
        serve_pwd = self.serve_sudo_pwd()
        subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'set', 'down', 'dev', interface_name], check=False)
        log.info('Interface down')

        serve_pwd = self.serve_sudo_pwd()
        p = subprocess.Popen(['/usr/bin/sudo', '-S', str(WG_PATH),
                              'setconf', interface_name, str(config_file)],
                              stdin=serve_pwd.stdout,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              )
        p.wait()
        log.info('Interface %s configured with %s', interface_name, config_file)
        err = p.stderr.read().decode()
        if p.returncode != 0:
            log.error('But failed!')
            log.error(p.stdout.read().decode())
            log.error(err.strip())
            return err

        log.info('Successfully')
        # TODO: check return codes
        serve_pwd = self.serve_sudo_pwd()
        subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'address', 'add', 'dev', interface_name, profile['ip_address']], 
                        stdin=serve_pwd.stdout,
                        check=True)
        log.info('Address set')

        # prepend dns entries to resolv.conf
        for dns in profile['dns_servers'].split(','):
            dns = dns.strip()
            if not dns:
                continue
            serve_pwd = self.serve_sudo_pwd()
            subprocess.run(['/usr/bin/sudo', '-S', 'sed', '-i','1i'+'nameserver '+ dns, '/run/resolvconf/resolv.conf'],
                            stdin=serve_pwd.stdout,
                            check=True)
            log.info('Added DNS server '+ dns +' to resolv.conf')

        serve_pwd = self.serve_sudo_pwd()
        subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'set', 'up', 'dev', interface_name],
                        stdin=serve_pwd.stdout,
                        check=True)
        log.info('Interface up')

        for extra_route in profile['extra_routes'].split(','):
            extra_route = extra_route.strip()
            if not extra_route:
                continue
            serve_pwd = self.serve_sudo_pwd()
            subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'route', 'add', extra_route, 'dev', interface_name],
                            stdin=serve_pwd.stdout,
                            check=True)

    def disconnect(self, interface_name):
        # It is fine to have this fail, it is only trying to cleanup before starting
        serve_pwd = self.serve_sudo_pwd()
        subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'del', 'dev', interface_name],
                       stdin=serve_pwd.stdout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False)

        # remove temporary dns entries, reset resolv.conf
        serve_pwd = self.serve_sudo_pwd()
        subprocess.run(['/usr/bin/sudo', '-S', 'resolvconf', '-u'],
                       stdin=serve_pwd.stdout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False)

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
