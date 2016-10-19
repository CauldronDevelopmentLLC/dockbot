# -*- python -*-
import os
import sys

from twisted.application import service
from twisted.python import log, logfile
from buildbot.slave.bot import BuildSlave

# Import environment
if os.path.exists('env.json'):
    import json
    env = json.load(open('env.json', 'r'))
    for name, value in env.items():
        os.environ[name] = os.path.expandvars(str(value))

# Scons options
if os.path.exists('scons-options.py') and 'SCONS_OPTIONS' not in os.environ:
    os.environ['SCONS_OPTIONS'] = os.getcwd() + '/scons-options.py'

# Get CPU count
try:
    import multiprocessing
    cpus = multiprocessing.cpu_count()
    if not 'SCONS_JOBS' in os.environ: os.environ['SCONS_JOBS'] = str(cpus)
    if not 'NCORES' in os.environ: os.environ['NCORES'] = str(cpus)
except: pass

# Buildmaster
host = os.getenv('DOCKBOT_MASTER_HOST')
port = os.getenv('DOCKBOT_MASTER_PORT')

basedir = os.getcwd()
slavename = os.getenv('CONTAINER_NAME')
passwd = os.getenv('SLAVE_PASS')
keepalive = 600
usepty = False
umask = 022
maxdelay = 300

# Don't leak this into the logs
del os.environ['SLAVE_PASS']

print 'Slave %s connecting to %s:%d' % (slavename, host, int(port))

logFile = logfile.LogFile.fromFullPath('slave.log')
log.addObserver(log.FileLogObserver(logFile).emit)

application = service.Application('buildslave')
s = BuildSlave(host, int(port), slavename, passwd, basedir, keepalive, usepty,
               umask = umask, maxdelay = maxdelay)
s.setServiceParent(application)
