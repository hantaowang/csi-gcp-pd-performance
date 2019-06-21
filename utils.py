import subprocess
import os
import json
import time

SHELL = True


class SingleTest:

    common_name = ''

    def __init__(self, gce_pd_dir, staging_image, kwargs):
        self.gce_pd_dir = gce_pd_dir
        self.staging_image = staging_image
        self.kwargs = kwargs

    def _run(self):
        raise NotImplementedError("cannot execute run for the generic test class")

    def run(self):
        self.setup()
        self._run()
        self.cleanup()

    def setup(self):
        pass

    def cleanup(self):
        pass

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
        c = os.environ.copy()
        c.update(env)
        env = c
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
        keys = [keys]
    if not isinstance(values, list):
        values = [values]
    for i in range(len(keys)):
        if values[i]:
            env[str(keys[i])] = str(values[i])
    return env


def record_results(time_finished, start, test_name):
    def to_local_str(t):
        return time.strftime("%m-%d-%Y-%H:%M:%S", time.localtime(t))

    s = json.dumps({
        'test_ran': test_name,
        'start': to_local_str(start),
        'time_taken': {k: v - start for k, v in time_finished.items()},
        'end': to_local_str(max(time_finished.values())),
    })
    os.makedirs("results", exist_ok=True)
    fname = "results/{}-{}-output.txt".format(test_name, to_local_str(start))
    with open(fname, 'w+') as out:
        out.write(s)
    print("Write results to {}".format(fname))
