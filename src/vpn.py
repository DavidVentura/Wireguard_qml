import subprocess
import time
import os
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

def can_use_kernel_module():
    if not Path('/usr/bin/sudo').exists():
        return False
    try:
        subprocess.run(['sudo', 'ip', 'link', 'add', 'test_wg0', 'type', 'wireguard'], check=True)
        subprocess.run(['sudo', 'ip', 'link', 'del', 'test_wg0', 'type', 'wireguard'], check=True)
    except subprocess.CalledProcessError:
        return False
    return True

def _connect(profile_name,  use_kmod):
    try:
        return interface._connect(get_profile(profile_name), PROFILES_DIR / profile_name / 'config.ini', use_kmod)
    except Exception as e:
        return str(e)

def genkey():
    return subprocess.check_output(['vendored/wg', 'genkey']).strip()

def genpubkey(privkey):
    p = subprocess.Popen(['vendored/wg', 'pubkey'],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,)

    stdout, stderr = p.communicate(privkey.encode())
    if p.returncode == 0:
        return stdout.strip()
    return stderr.strip()

def save_profile(profile_name, ip_address, private_key, interface_name, extra_routes, peers):
    if '/' in profile_name:
        return '"/" is not allowed in profile names'

    if len(private_key) != 44:
        return 'Peer key must be exactly 44 bytes long'

    _pub = genpubkey(private_key)
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

    PROFILE_DIR = PROFILES_DIR / profile_name
    PROFILE_DIR.mkdir(exist_ok=True, parents=True)

    PRIV_KEY_PATH = PROFILE_DIR / 'privkey'
    PROFILE_FILE = PROFILE_DIR / 'profile.json'
    CONFIG_FILE = PROFILE_DIR / 'config.ini'

    with PRIV_KEY_PATH.open('w') as fd:
        fd.write(private_key)

    profile = {'peers': peers,
               'ip_address': ip_address,
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
            fd.write(textwrap.dedent('''
            [Peer]
            #Name = {name}
            PublicKey = {key}
            AllowedIPs = {allowed_prefixes}
            Endpoint = {endpoint}
            PersistentKeepalive = 5
            '''.format_map(peer)))

def get_profile(profile):
    with (PROFILES_DIR / profile / 'profile.json').open() as fd:
        data = json.load(fd)
        return data

def list_profiles():
    profiles = []
    for path in PROFILES_DIR.glob('*/profile.json'):
        with path.open() as fd:
            data = json.load(fd)
            data.setdefault('interface_name', 'wg0')
            data['c_status'] = {}
            print(data, flush=True)
            profiles.append(data)
    return profiles
