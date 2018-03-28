import subprocess
import sys


def run(command_line):
    print("==> To run command : %s" % command_line)
    try:
        res = subprocess.check_output(command_line, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        res = e.output
    print "<== Output of command : %s" % res
    if "Error" in res or "fail" in res:
        sys.exit(100)
    return res
