import subprocess
from pathlib import Path

def test_sudo(sudo_pwd):
        if not Path('/usr/bin/sudo').exists():
            return False

        subprocess.run(['/usr/bin/sudo', '-k'])    
        try:
            serve_pwd = subprocess.Popen(['echo', sudo_pwd], stdout=subprocess.PIPE)
            subprocess.run(['/usr/bin/sudo', '-S', 'echo', 'Check for sudo'], stdin=serve_pwd.stdout, check=True)
        except subprocess.CalledProcessError:
            return False
        return True
