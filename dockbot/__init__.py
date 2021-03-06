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
from dockbot.RemoteImage import RemoteImage
from dockbot.RemoteSlave import RemoteSlave
from dockbot.util import *


args = {}

RUNNING = ('Running', 'green')
OFFLINE = ('Offline', 'blue')
NOT_FOUND = ('Not Found', 'magenta')
STARTING = ('Starting', 'Yellow')
STOPPING = ('Stopping', 'red')
BUILDING = ('Building', 'cyan')
BUILT = ('Built', 'white')
DELETING = ('Deleting', 'Red')
DIRTY = ('Dirty', 'red')
TRIGGERED = ('Triggered', 'cyan')
REMOTE = ('Remote', 'Magenta')

usage = '%(prog)s [OPTIONS] COMMAND [CONTAINER] [-- ARGS...]'

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
trigger              Trigger one or all builds on a running slave container.
publish              Publish a project's files.

'''


def version_type(s):
        if not re.match(r'^\d+\.\d+$', s):
            raise argparse.ArgumentTypeError('Must be <major>.<minor>')
        return s


def run():
    parser = argparse.ArgumentParser(
        usage = usage, description = description,
        formatter_class = argparse.RawTextHelpFormatter)
    parser._positionals.title = 'Positional arguments'
    parser._optionals.title = 'OPTIONS'

    parser.add_argument('cmd', metavar = 'COMMAND', nargs = '?',
                        default = 'status', help = cmd_help)
    parser.add_argument('name', metavar = 'NAME', nargs = '?',
                        help = 'Docker instance or container to operate on.  '
                        'Either "master", one of the slave or image names or '
                        'a glob pattern matching one or more slave or images '
                        'names.')
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
    parser.add_argument('-p', '--project',
                        help = 'Specify a specific project to trigger.')
    parser.add_argument('--release', default = 'alpha', choices = (
            'alpha', 'beta', 'public'), help = 'Release to publish.')
    parser.add_argument('--version', type = version_type,
                        help = 'Version to publish.  Latest version if '
                        'omitted.')
    parser.add_argument('--mode',
                        help = 'Build mode to publish.  Otherwise, all modes.')
    parser.add_argument('-c', '--continue', action = 'store_true',
                        dest='_continue',
                        help = 'Continue running if an operation fails.')
    parser.add_argument('--group', help = 'The system group to use when '
                        'publishing files.'),
    parser.add_argument('--fperms', default = 0o644, type = int,
                        help = 'The file permissions to use when publishing '
                        'files.'),
    parser.add_argument('--dperms', default = 0o755, type = int,
                        help = 'The directory permissions to use when '
                        'publishing files.'),
    parser.add_argument('--key', help = 'Path to the key file used for signing '
                        'published files.'),
    parser.add_argument('--password', help = 'Password used to unlock signing '
                        'key.  Will be prompted for if not supplied.'),
    parser.add_argument('--ts-url',
                        default = 'http://timestamp.comodoca.com/authenticode',
                        help = 'Time stamping URL used for signing published '
                        'files.'),

    global args
    args = parser.parse_args()

    try:
        dockbot.Dockbot(args)

    except dockbot.Error as e:
        print('\n%s\n' % e)
        sys.exit(1)
