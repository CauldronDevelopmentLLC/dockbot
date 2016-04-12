import argparse
import sys

import dockbot

#__all__ = 'Error Dockbot Config Image Container Slave Master'.split()
from dockbot.Error import Error
from dockbot.Dockbot import Dockbot
from dockbot.Config import Config
from dockbot.Image import Image
from dockbot.Container import Container
from dockbot.Slave import Slave
from dockbot.Master import Master
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

usage = '%(prog)s [OPTIONS] COMMAND [CONTAINER]'

description = '''
A tool for running a Buildbot master and set of slaves under Docker.
'''

cmd_help = '''
status     Print status then exit.
config     Print the instance config(s).
shell      Run shell in instance.
start      Start docker instance(s).
stop       Stop docker instance(s).
restart    Start then stop docker instance(s).
build      Build image(s).
rebuild    Rebuild image(s) from scratch.

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

    global args
    args = parser.parse_args()


    try:
        dockbot.Dockbot(args, 'dockbot.json')

    except dockbot.Error, e:
        print
        print e
        sys.exit(1)
