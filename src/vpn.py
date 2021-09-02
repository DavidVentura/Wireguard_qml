import subprocess
import time
import os
import base64
import json

from ipaddress import IPv4Network, IPv4Address
from pathlib import Path

CONFIG_DIR = Path('/home/phablet/.local/share/wireguard.davidv.dev')
PROFILES_DIR = CONFIG_DIR / 'profiles'

INTERFACE = 'wg0'

def _connect(profile_name):
    try:
        return connect(profile_name)
    except Exception as e:
        return str(e)
def connect(profile_name):
    profile = get_profile(profile_name)
    # It is fine to have this fail, it is only trying to cleanup before starting
    subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'del', 'dev', INTERFACE], check=False)

    # TODO: try to create via `ip` and validate if the kernel module is there
    p = subprocess.Popen(['/usr/bin/sudo', '-E', 'vendored/wireguard', 'wg0'],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       env={'WG_I_PREFER_BUGGY_USERSPACE_TO_POLISHED_KMOD': '1',
                            'WG_SUDO': '1'},
                       )

    p.wait()
    err = p.stderr.read().decode()
    print('stderr', err, flush=True)
    print('stdout', p.stdout.read().decode(), flush=True)
    print(p.returncode, flush=True)
    if p.returncode != 0:
        print("Dying", flush=True)
        return err

    PROFILE_DIR = PROFILES_DIR / profile_name
    PRIV_KEY_PATH = PROFILE_DIR / 'privkey'

    p = subprocess.Popen(['/usr/bin/sudo', 'vendored/wg',
                          'set', INTERFACE,
                          'private-key', str(PRIV_KEY_PATH),
                          'peer', profile['peer_key'],
                          'allowed-ips', profile['allowed_prefixes'],
                          'endpoint', profile['endpoint']],
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

def get_profile(profile):
    with (PROFILES_DIR / profile / 'profile.json').open() as fd:
        return json.load(fd)

def list_profiles():
    profiles = []
    for path in PROFILES_DIR.glob('*/profile.json'):
        with path.open() as fd:
            profiles.append(json.load(fd))
    return profiles
