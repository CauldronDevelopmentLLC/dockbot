# -*- python -*-
import os

from twisted.application import service
from buildbot.master import BuildMaster
from twisted.python.logfile import LogFile
from twisted.python.log import ILogObserver, FileLogObserver

logfile = LogFile.fromFullPath("twistd.log", rotateLength = 10000000)
application = service.Application('buildmaster')

application.setComponent(ILogObserver, FileLogObserver(logfile).emit)
BuildMaster(os.getcwd(), 'master.py').setServiceParent(application)
