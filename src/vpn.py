import subprocess
import time
import os

from pathlib import Path

# TODO: try to create via `ip` and validate if the kernel module is there
p = subprocess.Popen(['/usr/bin/sudo', '-E', 'vendored/wireguard', 'wg0'],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   env={'WG_I_PREFER_BUGGY_USERSPACE_TO_POLISHED_KMOD': '1',
                        'WG_SUDO': '1'},
                   )

'''
wg set wg0 private-key ./wg-key peer YLA3Gq/GW0QrQQfPA5wq7zfXnQI94a7oA8780hwHxWU= allowed-ips 10.88.88.1/32,192.168.2.0/24 endpoint vpn.davidv.dev:1194
sudo ip address add dev wg0 10.88.88.88/24
sudo ip link set up dev wg0
sudo ip r add 192.168.2.0/24  dev wg0
'''

'/home/phablet/.cache
p.wait(1)
print(p.stderr.read().decode(), flush=True)
print(p.stdout.read().decode(), flush=True)
print(p.returncode, flush=True)
#p = subprocess.run(['/usr/bin/sudo', 'whoami'], check=True, stdout=subprocess.PIPE)
#print(p.stdout, flush=True)
