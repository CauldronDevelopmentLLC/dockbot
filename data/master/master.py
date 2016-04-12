# -*- python -*-
import os
import re

from buildbot.buildslave import BuildSlave
from buildbot.changes.svnpoller import SVNPoller
from buildbot.changes.pb import PBChangeSource
from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.source import Git
from buildbot.steps.shell import Compile
from buildbot.steps.shell import ShellCommand
from buildbot.steps.shell import SetProperty
from buildbot.steps.transfer import FileUpload
from buildbot.steps.master import MasterShellCommand
from buildbot.steps.trigger import Trigger
from buildbot.scheduler import Triggerable
from buildbot.status import html
from buildbot.process.properties import WithProperties
from buildbot.process.buildstep import BuildStep
from buildbot.process.buildstep import SUCCESS, FAILURE

from twisted.python import log
from buildbot import buildset
from buildbot.scheduler import BaseScheduler, BaseUpstreamScheduler
from buildbot.sourcestamp import SourceStamp
from buildbot.status import builder

# Defaults
c = BuildmasterConfig = {}
c['change_source'] = [PBChangeSource()]
c['schedulers'] = []
c['status'] = []
c['builders'] = []
c['builder_info'] = {}
c['slaves'] = []
c['slave_info'] = {}
c['repo'] = {}
c['slavePortnum'] = os.environ.get('BUILDBOT_SLAVE_PORT', 9989)
c['httpPortnum'] = os.environ.get('BUILDBOT_HTTP_PORT', 8010)
c['buildbotURL'] = '//'
c['distURL'] = '//builds/'

warnPat = "(?!^scons).*: warning( [A-Z]+[0-9]+)?: "


class ChangeMatch:
    def __init__(self, pattern, repo = None, category = None):
        self.pattern = re.compile(pattern)
        self.repo = repo
        self.category = category


    def match(self, change):
        if self.category is not None and self.category != change.category:
            return False

        if change.repo is not None and self.repo is not None and \
                change.repo != self.repo:
            return False

        for f in change.files:
            if self.pattern.match(f): return True

        return False

    def __str__(self):
        return "Change match:%s Category:%s Repo:%s" % (
            self.pattern.pattern, self.category, self.repo)


BUILDER_IDLE = 0
BUILDER_TRIGGERED = 1
BUILDER_RUNNING = 2
BUILDER_FAILED = 4

class BuilderInfo:
    def __init__(self, name, change_matches = [], deps = [], priority = 0):
        self.name = name
        self.change_matches = list(change_matches)
        self.deps = set(deps)
        self.depof = set()
        self.state = BUILDER_IDLE
        self.failed = False
        self.changes = []
        self.priority = priority

        for dep in self.deps:
            dep.depof.add(self)


    def addChange(self, change):
        for m in self.change_matches:
            if m.match(change):
                deps = ','.join(map(lambda x: x.name, self.deps))
                log.msg("Change match:%s Category:%s Repo:%s Name:%s " \
                            "Deps:%s" % (
                        m.pattern.pattern, change.category, change.repo,
                        self.name, deps))

                self.changes.append(change)
                self.trigger()
                break


    def trigger(self):
        if self.state & BUILDER_TRIGGERED: return
        self.state |= BUILDER_TRIGGERED
        for builder in self.depof:
            builder.trigger()


    def is_ready(self):
        if self.state & BUILDER_RUNNING: return False
        if not self.state & BUILDER_TRIGGERED: return False

        for dep in self.deps:
            if dep.state != BUILDER_IDLE: return False

        return True


    def has_cycle(self, visited = set()):
        if self.name in visited: return True
        visited.add(self.name)

        for dep in self.deps:
            if dep.has_cycle(visited):
                return True

        visited.remove(self.name)
        return False


    def __cmp__(self, other):
        if self.priority == other.priority:
            return cmp(self.name, other.name)
        return other.priority - self.priority


    def __hash__(self):
        return self.name.__hash__()



class DepScheduler(BaseUpstreamScheduler):
    compare_attrs = ('name', 'treeStableTimer', 'builders',
                     'properties', 'categories')


    def __init__(self, name, builders, treeStableTimer, properties = {}):
        BaseUpstreamScheduler.__init__(self, name, properties)
        self.builders = builders[:]
        self.builders.sort()
        self.treeStableTimer = treeStableTimer

        # Check for dependency cycles
        self.builder_map = {}
        for builder in self.builders:
            if builder.has_cycle():
                raise Exception, "Detected cycle in builder dependencies."

            self.builder_map[builder.name] = builder


    def listBuilderNames(self):
        return map(lambda x: x.name, self.builders)


    def getPendingBuildTimes(self):
        return []


    def addChange(self, change):
        log.msg("Adding change:%s" % change.asText())

        # Ignore revisions, they cause problems triggering off other repos
        change.revision = None  # Always build latest

        map(lambda x: x.addChange(change), self.builders)
        self.scheduleBuilders()


    def scheduleBuilders(self):
        ready = filter(lambda x: x.is_ready(), self.builders)
        if not len(ready): return False

        for builder in ready:
            bs = buildset.BuildSet(
                [builder.name], SourceStamp(changes = builder.changes),
                properties = self.properties)

            builder.state &= ~BUILDER_TRIGGERED
            builder.state |= BUILDER_RUNNING

            d = bs.waitUntilFinished()
            d.addCallback(self.buildSetFinished)
            BaseScheduler.submitBuildSet(self, bs)

        return True


    def buildSetFinished(self, bs):
        #if not self.running: return

        name = bs.builderNames[0]
        log.msg("Build finished %s" % name)

        bldr = self.builder_map[name]
        bldr.state &= ~BUILDER_RUNNING

        if bs.getResults() == builder.SUCCESS:
            bldr.state &= ~BUILDER_FAILED

            if not self.scheduleBuilders():
                ss = bs.getSourceStamp()
                map(lambda w: w(ss), self.successWatchers)

        else: bldr.state |= BUILDER_FAILED


def add_slave(name, password, types, root, max_builds = 1, configs = None,
              projects = None):
    root = os.path.expanduser(root)
    if isinstance(types, str): types = types.split()
    if isinstance(configs, str): configs = configs.split()
    if isinstance(projects, str): projects = projects.split()

    if projects:
        for project in projects:
            add_slave(name + '-' + project, password, types + [project], root,
                      max_builds, configs)

    elif configs:
        for config in configs:
            add_slave(name + '-' + config, password, types, root, max_builds)

    else:
        properties = {
            'root': root, 'types': set(types), 'builders': [], 'env': {}}
        c['slaves'].append(BuildSlave(name, password, max_builds,
                                      properties = properties))
        c['slave_info'][name] = properties


def get_slaves_by_type(types):
    if isinstance(types, str): types = types.split()
    types = set(types)

    return filter(lambda slave: types.issubset(c['slave_info'][slave]['types']),
                  c['slave_info'].keys())


def make_change_matches(matches, default_branch):
    change_matches = []

    for match in matches:
        if hasattr(match, '__iter__'): category, branch = match
        else: category, branch = match, default_branch
        change_matches.append(ChangeMatch('^' + re.escape(branch + '/'),
                                          category = category))

    return change_matches


def add_builder(project, slave, factory, home_var, branch, category, deps,
                priority, change_deps = []):
    slave_info = c['slave_info'][slave]
    env = slave_info['env']

    # HOME environment variable
    if not home_var: home_var = project.upper().replace('-', '_') + '_HOME'
    env[home_var] = '%(root)s/%(slave)s/' + project + '/build'

    # Resolve builder environment
    name = '%s-%s' % (slave, project)
    dir = '%s/%s' % (slave, project)

    vars = slave_info.copy()
    vars['slave'] = slave
    vars['project'] = project
    vars['builder'] = name

    resolved_env = {}
    for key in env.keys():
        resolved_env[key] = env[key] % vars

    c['builders'].append(
        {'name': name, 'slavename': slave, 'builddir': dir, 'factory': factory,
         'env': resolved_env, 'category': project})

    change_matches = [ChangeMatch('.*', category = category)]

    bdeps = []
    for dep in deps:
        dep_name =  '%s-%s' % (slave, dep)
        if c['builder_info'].has_key(dep_name):
            bdeps.append(c['builder_info'][dep_name])

    c['builder_info'][name] = BuilderInfo(name, change_matches, bdeps, priority)
    c['slave_info'][slave]['builders'].append(name)


def make_repo_step(name, branch = None, mode = 'update'):
    info = c['repo'][name]
    kwargs = {'mode': mode, 'retry': (60, 5)}

    if info['type'] == 'svn':
        url = info['url']
        if branch: url += '/' + branch

        kwargs['svnurl'] = url
        if info.has_key('user'): kwargs['username'] = info['user']
        if info.has_key('pass'): kwargs['password'] = info['pass']

        return SVN(**kwargs)

    elif info['type'] == 'git' or info['type'] == 'github':
        if info['type'] == 'github' and not 'url' in info:
            kwargs['repourl'] = 'git@github.com:%s/%s.git' % (
                info['org'], info.get('name', name))

        else: kwargs['repourl'] = info['url']

        if branch: kwargs['branch'] = branch
        kwargs['submodules'] = info.get('submodules', False)

        return Git(**kwargs)

    else: raise Exception, 'Unrecognized repo type "%s"' % info['type']


def add_package_build(type, factory, compile_command):
    build = '%(slavename)s'

    # Build
    cmd = compile_command + [type]
    factory.addStep(Compile(description = [type], descriptionDone = [type],
                            command = cmd, warningPattern = warnPat))

    # Get file name
    factory.addStep(SetProperty(command = 'cat %s.txt' % type,
                                property = 'package_name'))

    # Get file
    src = '%(package_name)s'
    file = '/tmp/%(slavename)s/' + src
    step = FileUpload(slavesrc = WithProperties(src),
                      masterdest = WithProperties(file))
    step.haltOnFailure = True
    step.flunkOnFailure = True
    factory.addStep(step)

    # Publish
    cmd = WithProperties('./publish.py build ' + file + \
                             ' %(slavename)s %(got_revision)s %(buildnumber)s')
    MasterShellCommand.haltOnFailure = True
    MasterShellCommand.flunkOnFailure = True
    step = MasterShellCommand(command = cmd, property = 'publish_path',
                              url = (src, c['distURL'] + '%(publish_path)s'),
                              name = 'publish ' + type)
    factory.addStep(step)


def add_build_project(
    name, repo, branch = None, slaves = [], compile_command = ['scons', '-k'],
    home_var = None, env = {}, deps = [], test = False, priority = 0,
    packages = [], build = True, change_deps = []):

    if isinstance(deps, str): deps = deps.split()
    if isinstance(packages, str): packages = packages.split()

    f = factory.BuildFactory()
    f.useProgress = False
    f.addStep(make_repo_step(repo, branch))

    if build:
        f.addStep(Compile(command = compile_command, warningPattern = warnPat))

    if test:
        if isinstance(test, str): test_dir = test
        else: test_dir = 'tests'

        cmd = [test_dir + '/testHarness', '--no-color', '-C', test_dir,
               '--build', '--diff-failed', '--view-failed', '--view-unfiltered',
               '--save-failed']
        f.addStep(ShellCommand(description = 'testing',
                               descriptionDone = 'tests', command = cmd,
                               haltOnFailure = True))

    for package in packages:
        add_package_build(package, f, compile_command)

    # Add to slaves
    for slave in slaves:
        add_builder(name, slave, f, home_var, branch, repo, list(deps),
                    priority, list(change_deps))



class TriggerBuilderInfo(BuildStep):
    def __init__(self, builderNames = None, **kwargs):
        if builderNames is None:
            raise TypeError('argument builderNames is required')

        self.builderNames = builderNames

        BuildStep.__init__(self, **kwargs)

        self.addFactoryArguments(builderNames = builderNames)

    def start(self):
        for name in self.builderNames:
            info = c['builder_info'][name]
            info.state = BUILDER_TRIGGERED

        self.finished(SUCCESS)


def add_build_all():
    for slave, vars in c['slave_info'].items():
        name = slave + '-all'

        sched = Triggerable(name = name, builderNames = vars['builders'])
        c['schedulers'].append(sched)

        f = factory.BuildFactory()
        f.useProgress = False
        f.addStep(Trigger(schedulerNames = [name], waitForFinish = False))
        c['builders'].append(
            {'name': name, 'slavename': slave, 'builddir': slave + '/all',
             'factory': f, 'category': 'all'})


# Import local configuration
execfile('local.cfg')


# Finish up
add_build_all()

c['schedulers'].append(DepScheduler('quick', c['builder_info'].values(), 0))

c['status'].append(
    html.WebStatus(http_port = c['httpPortnum'], allowForce = True))
