import inspect, os

DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

execfile(DIR + '/data/bin/publish')
