import vpn
import subprocess
import os
import stat

from pathlib import Path

def sudo(command_lst, pwd):
    serve_pwd = subprocess.Popen(['echo', pwd], stdout=subprocess.PIPE)
    return subprocess.run(['/usr/bin/sudo', '-S'] + command_lst, stdin=serve_pwd.stdout, check=True)

def needs_sudo():
    s = os.stat(str(vpn.DAEMON_PATH))
    is_setuid = s.st_mode & stat.S_ISUID
    is_owned_by_root = s.st_uid == 0
    if is_setuid and is_owned_by_root:
        return False
    return True

def setuid_daemon(sudo_pwd):
    try:
        sudo(["chown", "root:root", str(vpn.DAEMON_PATH)], sudo_pwd)
        sudo(["chmod", "4755", str(vpn.DAEMON_PATH)], sudo_pwd)
        return True
    except Exception as e:
        print(str(e), flush=True)
        return str(e)
