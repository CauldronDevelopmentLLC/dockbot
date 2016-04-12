# -*- python -*-
import os

from twisted.application import service
from buildbot.slave.bot import BuildSlave

port = 9989
host = os.getenv('BUILDMASTER_PORT_9989_TCP_ADDR')

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

application = service.Application('buildslave')
s = BuildSlave(host, int(port), slavename, passwd, basedir, keepalive, usepty,
               umask = umask, maxdelay = maxdelay)
s.setServiceParent(application)
