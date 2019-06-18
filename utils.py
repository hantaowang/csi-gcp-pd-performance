import subprocess
import os

SHELL = True


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def execute(args, hide_output=False, env=None, hide_cmd=False):
    for i in range(len(args)):
        if not any(map(lambda x: isinstance(args[i], x), [str, bytes, os.PathLike])):
            args[i] = str(args[i])
    if not hide_cmd:
        print(bcolors.OKGREEN + "EXECUTING:" + bcolors.ENDC, args)
    if env:
        env.update(os.environ)
    try:
        out = subprocess.check_output(args, stderr=subprocess.STDOUT, env=env)
    except subprocess.CalledProcessError as e:
        out = e.output
    out = out.decode("utf-8")
    if not hide_output:
        print(bcolors.OKGREEN + "OUTPUT:" + bcolors.ENDC)
        print(out)
    return out


def set_env_if_true(keys, values):
    env = {}
    if not isinstance(keys, list):
        keys = list(keys)
    if not isinstance(values, list):
        keys = list(keys)
    for i in range(len(keys)):
        if values[i]:
            env[str(keys[i])] = str(values[i])
    return env