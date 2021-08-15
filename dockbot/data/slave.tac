# -*- python -*-
import os
import sys

from twisted.application import service
from twisted.python import log, logfile
from buildbot.slave.bot import BuildSlave

if 'PWD' not in os.environ: os.environ['PWD'] = os.getcwd()

# Import environment
if os.path.exists('env.json'):
    import json
    env = json.load(open('env.json', 'r'))
    for name, value in list(env.items()):
        if value is None:
            if name in os.environ: del os.environ[name]
        else:
            if isinstance(value, (list, tuple)):
                value = os.pathsep.join(map(str, value))
            os.environ[name] = os.path.expandvars(str(value))

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
slavename = os.getenv('SLAVE_NAME')
passwd = os.getenv('SLAVE_PASS')
keepalive = 600
usepty = False
umask = 0o22
maxdelay = 300

# Don't leak this into the logs
del os.environ['SLAVE_PASS']

print('Slave %s connecting to %s:%d' % (slavename, host, int(port)))

logFile = logfile.LogFile.fromFullPath('slave.log')
log.addObserver(log.FileLogObserver(logFile).emit)

application = service.Application('buildslave')
s = BuildSlave(host, int(port), slavename, passwd, basedir, keepalive, usepty,
               umask = umask, maxdelay = maxdelay)
s.setServiceParent(application)
