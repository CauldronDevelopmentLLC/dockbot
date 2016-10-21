# -*- python -*-
import os

from twisted.application import service
from buildbot.master import BuildMaster
from twisted.python.logfile import LogFile
from twisted.python.log import ILogObserver, FileLogObserver

# Import environment
if os.path.exists('env.json'):
    import json
    env = json.load(open('env.json', 'r'))
    for name, value in env.items():
        if value is None:
            if name in os.environ: del os.environ[name]
        else: os.environ[name] = os.path.expandvars(str(value))

logfile = LogFile.fromFullPath("twistd.log", rotateLength = 10000000)
application = service.Application('buildmaster')

application.setComponent(ILogObserver, FileLogObserver(logfile).emit)
BuildMaster(os.getcwd(), 'master.py').setServiceParent(application)
