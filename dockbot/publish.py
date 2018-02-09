import inspect, os

DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

exec(open(DIR + '/data/bin/publish', 'r').read())
