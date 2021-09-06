import struct
import socket
import subprocess
import time
import os
import sys
import logging

import interface
import vpn

from pathlib import Path

LOG_DIR = Path('/home/phablet/.cache/wireguard.davidv.dev')
log = None

def get_preferred_def_route():
    metric = 999999999
    ip = None
    for line in open('/proc/net/route').readlines():
        line = line.split()
        if line[1] != '00000000' or not int(line[3], 16) & 2:
            # If not default route or not RTF_GATEWAY, skip it
            continue

        _ip = socket.inet_ntoa(struct.pack("<L", int(line[2], 16)))
        _metric = int(line[6])
        if _metric > metric:
            continue
        metric = _metric
        ip = _ip
    return ip


def keep_tunnel(profile_name):

    PROFILE_DIR = vpn.PROFILES_DIR / profile_name
    CONFIG_FILE = PROFILE_DIR / 'config.ini'

    route = get_preferred_def_route()
    profile = vpn.get_profile(profile_name)
    interface_name = profile['interface_name']
    interface_file = Path('/sys/class/net/') / interface_name
    bring_up_interface(interface_name)

    log.info('Setting up tunnel')
    interface.config_interface(profile, CONFIG_FILE)
    log.info('Tunnel is up')

    while interface_file.exists():
        new_route = get_preferred_def_route()
        if route == new_route:
            log.debug('Routes did not change, sleeping')
            time.sleep(2)
            continue
        log.info('New route via %s, reconfiguring interface', new_route)
        route = new_route
        interface.config_interface(profile, CONFIG_FILE)
    log.info("Interface %s no longer exists. Exiting", interface_name)

def bring_up_interface(interface_name):
    log.info('Bringing up %s', interface_name)
    p = subprocess.Popen(['/usr/bin/sudo', '-E',
                          'vendored/wireguard',
                          interface_name],
                          #'--log', str(LOG_DIR / 'boring.log'),
                          #'--verbosity', 'info',
                          #interface_name],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          stdin=subprocess.DEVNULL,
                          env={'WG_I_PREFER_BUGGY_USERSPACE_TO_POLISHED_KMOD': '1',
                               'WG_SUDO': '1',
                               },
                          start_new_session=True,
                       )
    p.wait()

    if p.returncode != 0:
        log.error('Failed to execute wireguard')
        log.error('stdout: %s', p.stdout.read())
        log.error('stderr: %s', p.stderr.read())

def daemonize():
    """
    do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == '__main__':
    profile_name = sys.argv[1]
    logging.basicConfig(filename=str(LOG_DIR / 'daemon-{}.log'.format(profile_name)),
                        level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(name)s %(message)s')
    log = logging.getLogger()
    log.info('Started daemon with args: %s', sys.argv)
    log.info('Daemonizing')
    daemonize()
    log.info('Successfully daemonized')
    try:
        keep_tunnel(profile_name)
    except Exception as e:
        log.exception(e)
    log.info('Exiting')
