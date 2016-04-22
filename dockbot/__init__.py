import argparse
import sys

import dockbot

from dockbot.Error import Error
from dockbot.Dockbot import Dockbot
from dockbot.Config import Config
from dockbot.Image import Image
from dockbot.Container import Container
from dockbot.Slave import Slave
from dockbot.Master import Master
from dockbot.util import *


args = {}

CONFIG = 'dockbot.json'

RUNNING = ('Running', 'green')
OFFLINE = ('Offline', 'blue')
NOT_FOUND = ('Not Found', 'magenta')
STARTING = ('Starting', 'Yellow')
STOPPING = ('Stopping', 'red')
BUILDING = ('Building', 'cyan')
BUILT = ('Built', 'white')
DELETING = ('Deleting', 'Red')
DIRTY = ('Dirty', 'red')

usage = '%(prog)s [OPTIONS] COMMAND [CONTAINER]'

description = '''
A tool for running a Buildbot master and set of slaves under Docker.
'''

cmd_help = '''
status               Print status then exit.
config               Print the instance config(s).
shell                Run shell in instance.
start                Start docker instance(s).
stop                 Stop docker instance(s).
restart              Start then stop docker instance(s).
build                Build image(s).
delete               Delete an image or container.
trigger [PROJECT]    Trigger one or all builds on a running slave container.

'''


def run():
    parser = argparse.ArgumentParser(
        usage = usage, description = description,
        formatter_class = argparse.RawTextHelpFormatter)
    parser._positionals.title = 'Positional arguments'
    parser._optionals.title = 'OPTIONS'

    parser.add_argument('cmd', metavar = 'COMMAND', nargs = '?',
                        default = 'status', help = cmd_help)
    parser.add_argument('name', metavar = 'NAME', nargs = '?',
                        help = 'Docker instance or container to operate on.  ' +
                        'Either "master" or one of the slave names.')
    parser.add_argument('project', metavar = 'PROJECT', nargs = '?',
                        help = 'A project name.')
    parser.add_argument('args', metavar = 'ARGS', nargs = '*',
                        help = 'Extra arguments to pass on to Docker')
    parser.add_argument('--slaves', metavar = 'DIR', default = 'slaves',
                        help = 'Slave directory')
    parser.add_argument('--width', metavar = 'NUMBER', default = 80, type = int,
                        help = 'Status line width')
    parser.add_argument('-v', '--verbose', action = 'store_true',
                        help = 'Verbose output')
    parser.add_argument('-f', '--foreground', action = 'store_true',
                        help = 'Run in foreground')
    parser.add_argument('--force', action = 'store_true',
                        help = 'Run even if container is dirty')
    parser.add_argument('-a', '--all', action = 'store_true',
                        help = 'Perform all prerequisite actions automatically')

    global args
    args = parser.parse_args()

    try:
        if not os.path.exists(CONFIG):
            raise dockbot.Error(
                'ERROR: `%s` not found in the current directory.\nMust be '
                'run in the top-level directory of a dockbot configuration.' %
                CONFIG)

        dockbot.Dockbot(args, CONFIG)

    except dockbot.Error, e:
        print '\n%s\n' % e
        sys.exit(1)
