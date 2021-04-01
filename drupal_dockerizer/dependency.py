import os
from subprocess import Popen


def check_tool(name):
    try:
        devnull = open(os.devnull)
        Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        raise SystemExit(f"ERROR: Drupal Dockerizer requires program {name}\n\r{e}")
    return True
