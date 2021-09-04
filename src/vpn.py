import subprocess
import time
import os
import base64
import json
import textwrap
import socket

import daemon
import interface

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

def _connect(profile_name):
    try:
        return interface._connect(get_profile(profile_name), PROFILES_DIR / profile_name / 'config.ini')
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

def save_profile(profile_name, peer_key, allowed_prefixes, ip_address, endpoint, private_key, extra_routes):
    if '/' in profile_name:
        return '"/" is not allowed in profile names'

    if len(peer_key) != 44:
        return 'Peer key must be exactly 44 bytes long'

    if len(private_key) != 44:
        return 'Peer key must be exactly 44 bytes long'

    _pub = genpubkey(private_key)
    if len(_pub) != 44:
        return 'Bad private key: ' + _pub
    try:
        base64.b64decode(peer_key)
    except Exception as e:
        return 'Bad peer key'

    if ':' not in endpoint:
        return 'Bad endpoint -- missing ":"'

    try:
        base64.b64decode(private_key)
    except Exception as e:
        return 'Bad private key'

    for allowed_prefix in allowed_prefixes.split(','):
        allowed_prefix = allowed_prefix.strip()
        try:
            IPv4Network(allowed_prefix, strict=False)
        except Exception as e:
            return 'Bad prefix ' + allowed_prefix + ': ' + str(e)

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

    profile = {'peer_key': peer_key,
               'allowed_prefixes': allowed_prefixes,
               'ip_address': ip_address,
               'endpoint': endpoint,
               'extra_routes': extra_routes,
               'profile_name': profile_name,
               'private_key': private_key,
               }
    with PROFILE_FILE.open('w') as fd:
        json.dump(profile, fd, indent=4, sort_keys=True)

    with CONFIG_FILE.open('w') as fd:
        fd.write(textwrap.dedent('''
        [Interface]
        PrivateKey = {private_key}

        [Peer]
        PublicKey = {peer_key}
        AllowedIPs = {allowed_prefixes}
        Endpoint = {endpoint}
        PersistentKeepalive = 5
        '''.format_map(profile)).strip())

def get_profile(profile):
    with (PROFILES_DIR / profile / 'profile.json').open() as fd:
        return json.load(fd)

def list_profiles():
    profiles = []
    for path in PROFILES_DIR.glob('*/profile.json'):
        with path.open() as fd:
            profiles.append(json.load(fd))
    return profiles
