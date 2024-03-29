import os
import subprocess
import shlex
import shutil
import pipes
import json
import re
from pkg_resources import Requirement, resource_filename
import requests
import dockbot


ANSI_COLORS = 'black red green yellow blue magenta cyan white'.split()
ANSI_CLEAR = '\033[0m'


def ansi_code(color = 'black', fg = True, intense = False):
    if color not in ANSI_COLORS:
        if color.lower() in ANSI_COLORS:
            color = color.lower()
            intense = True

        else: raise dockbot.Error('Invalid ANSI color "%s"' % color)

    color = ANSI_COLORS.index(color)

    if fg: color += 30
    else: color += 40
    if intense: color += 60

    return '\033[%dm' % color


def status_line(left, right, color):
    padding = dockbot.args.width - len(left) - len(right) - 2
    print('%s%s%s[%s]%s' %
          (left, ' ' * padding, ansi_code(color), right, ANSI_CLEAR))


def publish_file(source, dest):
    target = os.path.join(dest, os.path.basename(source))

    if os.path.exists(target): os.unlink(target)
    if dockbot.args.verbose: print('%s -> %s' % (source, target))
    shutil.copy(source, target)


def system(cmd, redirect = False, err_action = None, **kwargs):
    if isinstance(cmd, str): cmd = shlex.split(cmd)

    if dockbot.args.verbose:
        print('@', ' '.join(pipes.quote(s) for s in cmd))

    if redirect:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE

    p = subprocess.Popen(cmd, **kwargs)
    out, err = p.communicate()

    if p.returncode and err_action is not None:
        msg = 'Failed to %s' % err_action
        if err: msg += ': \n' + err.strip()

        raise dockbot.Error(msg)

    if redirect: return p.returncode, out, err
    return p.returncode


def inspect(name):
    ret, out, err = system(['docker', 'inspect', name], True)
    if ret: return dockbot.NOT_FOUND
    return json.loads(out)


def mkdirs(path):
    if not os.path.exists(path): os.makedirs(path)


def touch(path):
    open(path, 'a')


def get_resource(path):
    return resource_filename(Requirement.parse('dockbot'), path)


def trigger(name, project, conf):
    url = 'http://%s:%d/builders/%s-%s/force' % (
        conf['host'], int(conf['http-port']), name, project)

    if dockbot.args.verbose: print('triggering', url)

    r = requests.get(url)
    if r.status_code != 200:
        msg = 'Failed to trigger build, possibly an HTTP proxy problem.'
        if dockbot.args.verbose: msg += '\n' + r.text
        raise dockbot.Error(msg)

    dockbot.status_line("%s-%s" % (conf['namespace'], name), *dockbot.TRIGGERED)


def copy_tree(src, dst):
    for root, subdirs, files in os.walk(src):
        target_dir = re.sub(r'^' + src, dst, root)
        mkdirs(target_dir)

        for filename in files:
            publish_file(root + '/' + filename, target_dir)
