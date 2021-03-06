import subprocess
import time
import os
import shutil
import base64
import json
import textwrap
import socket

import interface
import daemon

from ipaddress import IPv4Network, IPv4Address
from pathlib import Path

CONFIG_DIR = Path('/home/phablet/.local/share/wireguard.davidv.dev')
PROFILES_DIR = CONFIG_DIR / 'profiles'
LOG_DIR = Path('/home/phablet/.cache/wireguard.davidv.dev')


LOG_DIR.mkdir(parents=True, exist_ok=True)

class Vpn:
    def __init__(self):
        self._pwd = ''

    def set_pwd(self, sudo_pwd):
        self._sudo_pwd = sudo_pwd;
        self.interface = interface.Interface(sudo_pwd)

    def serve_sudo_pwd(self):
        return subprocess.Popen(['echo', self._sudo_pwd], stdout=subprocess.PIPE)

    def can_use_kernel_module(self):
        if not Path('/usr/bin/sudo').exists():
            return False
        try:
            serve_pwd = self.serve_sudo_pwd()
            subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'add', 'test_wg0', 'type', 'wireguard'], stdin=serve_pwd.stdout, check=True)
            serve_pwd = self.serve_sudo_pwd()
            subprocess.run(['/usr/bin/sudo', '-S', 'ip', 'link', 'del', 'test_wg0', 'type', 'wireguard'], stdin=serve_pwd.stdout, check=True)
        except subprocess.CalledProcessError:
            return False
        return True

    def _connect(self, profile_name,  use_kmod):
        try:
            return self.interface._connect(self.get_profile(profile_name), PROFILES_DIR / profile_name / 'config.ini', use_kmod)
        except Exception as e:
            return str(e)

    def genkey(self):
        return subprocess.check_output(['vendored/wg', 'genkey']).strip()

    def genpubkey(self, privkey):
        p = subprocess.Popen(['vendored/wg', 'pubkey'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,)

        stdout, stderr = p.communicate(privkey.encode())
        if p.returncode == 0:
            return stdout.strip()
        return stderr.strip()

    def save_profile(self, profile_name, ip_address, private_key, interface_name, extra_routes, dns_servers, peers):
        if '/' in profile_name:
            return '"/" is not allowed in profile names'

        if len(private_key) != 44:
            return 'Peer key must be exactly 44 bytes long'

        _pub = self.genpubkey(private_key)
        if len(_pub) != 44:
            return 'Bad private key: ' + _pub

        try:
            IPv4Network(ip_address, strict=False)
        except Exception as e:
            return 'Bad ip address: ' + str(e)

        try:
            base64.b64decode(private_key)
        except Exception as e:
            return 'Bad private key'

        for peer in peers:
            if not peer['name']:
                return 'Peer name is incomplete'

            if len(peer['key']) != 44:
                return 'Peer key ({name}) must be exactly 44 bytes long'.format_map(peer)
            try:
                base64.b64decode(peer['key'])
            except Exception as e:
                return 'Bad peer ({name}) key'.format_map(peer)

            if ':' not in peer['endpoint']:
                return 'Bad endpoint ({name}) -- missing ":"'.format_map(peer)

            if len(peer['presharedKey']) > 0 and len(peer['presharedKey']) != 44:
                return 'Preshared key ({name}) must be exactly 44 bytes long'.format_map(peer)
            try:
                base64.b64decode(peer['presharedKey'])
            except Exception as e:
                return 'Bad peer ({name}) preshared key'.format_map(peer)

            allowed_prefixes = peer['allowed_prefixes']
            for allowed_prefix in allowed_prefixes.split(','):
                allowed_prefix = allowed_prefix.strip()
                try:
                    IPv4Network(allowed_prefix, strict=False)
                except Exception as e:
                    return 'Bad peer ({name}) prefix '.format_map(peer) + allowed_prefix + ': ' + str(e)

        if extra_routes:
            for route in extra_routes.split(','):
                route = route.strip()
                try:
                    IPv4Network(route, strict=False)
                except Exception as e:
                    return 'Bad route ' + route + ': ' + str(e)

        if dns_servers:
            for dns in dns_servers.split(','):
                dns = dns.strip()
                try:
                    IPv4Network(dns, strict=False)
                except Exception as e:
                    return 'Bad dns ' + dns + ': ' + str(e)

        PROFILE_DIR = PROFILES_DIR / profile_name
        PROFILE_DIR.mkdir(exist_ok=True, parents=True)

        PRIV_KEY_PATH = PROFILE_DIR / 'privkey'
        PROFILE_FILE = PROFILE_DIR / 'profile.json'
        CONFIG_FILE = PROFILE_DIR / 'config.ini'

        with PRIV_KEY_PATH.open('w') as fd:
            fd.write(private_key)

        profile = {'peers': peers,
                   'ip_address': ip_address,
                   'dns_servers': dns_servers,
                   'extra_routes': extra_routes,
                   'profile_name': profile_name,
                   'private_key': private_key,
                   'interface_name': interface_name,
                   }
        with PROFILE_FILE.open('w') as fd:
            json.dump(profile, fd, indent=4, sort_keys=True)

        with CONFIG_FILE.open('w') as fd:
            fd.write(textwrap.dedent('''
            [Interface]
            #Profile = {profile_name}
            PrivateKey = {private_key}
            ''').format_map(profile))
            for peer in peers:
                if len(peer['presharedKey']) > 0:
                    fd.write(textwrap.dedent('''
                    [Peer]
                    #Name = {name}
                    PublicKey = {key}
                    AllowedIPs = {allowed_prefixes}
                    Endpoint = {endpoint}
                    PresharedKey = {presharedKey}
                    PersistentKeepalive = 5
                    '''.format_map(peer)))
                else:
                    fd.write(textwrap.dedent('''
                    [Peer]
                    #Name = {name}
                    PublicKey = {key}
                    AllowedIPs = {allowed_prefixes}
                    Endpoint = {endpoint}
                    PersistentKeepalive = 5
                    '''.format_map(peer)))

    def delete_profile(self, profile):
        print(profile)
        PROFILE_DIR = PROFILES_DIR / profile
        print(PROFILE_DIR)
        try:
            shutil.rmtree(PROFILE_DIR.as_posix())
        except OSError as e:
            return 'Error: ' + PROFILE_DIR + ': ' + e.strerror


    def get_profile(self, profile):
        with (PROFILES_DIR / profile / 'profile.json').open() as fd:
            data = json.load(fd)
            return data

    def list_profiles(self):
        profiles = []
        for path in PROFILES_DIR.glob('*/profile.json'):
            with path.open() as fd:
                data = json.load(fd)
                data.setdefault('interface_name', 'wg0')
                data['c_status'] = {}
                print(data, flush=True)
                profiles.append(data)
        return profiles

instance = Vpn()
