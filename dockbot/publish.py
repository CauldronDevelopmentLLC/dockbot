#!/usr/bin/python

import sys
import os
import re
import shutil
import inspect
import grp
import filecmp
import glob
import subprocess
from optparse import OptionParser, Option


__dir__ = os.path.dirname(inspect.getfile(inspect.currentframe()))


def parse_package_version(name):
    m = re.match(r'(?P<project>[\w_-]+)[_-]'
                 r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<rev>\d+)[\._-]', name)
    if not m:
        raise Exception("Failed to parse package version '%s'" % name)

    return m.group('project', 'major', 'minor', 'rev')


def parse_slave_name(name):
    m = re.match(r'(?P<slave>[^_-]+[_-][^_-]+[_-][^_-]+)-([a-z0-9]+-)*'
                 r'(?P<mode>[a-z]+)$', name)

    if not m:
        raise Exception("Failed to parse slave name '%s'" % name)

    return m.group('slave', 'mode')


def correct_perms(path):
    umask = os.umask(0777)
    if os.path.isdir(path): os.chmod(path, options.dperms)
    else: os.chmod(path, options.fperms)
    os.lchown(path, -1, grp.getgrnam(options.group)[2])
    os.umask(umask)


def ensure_dir(path):
    if os.path.exists(path): return

    # Make sure parent exists
    parent, child = os.path.split(os.path.normpath(path))
    if parent and parent != path: ensure_dir(parent)

    # Create directory with correct permissions and group
    os.mkdir(path, options.dperms)
    os.lchown(path, -1, grp.getgrnam(options.group)[2])


def force_link(src, dst):
    if os.path.islink(dst): os.remove(dst)
    os.symlink(src, dst)
    correct_perms(dst)


def publish_file(src, target, force):
    if os.path.isdir(target): dst = target + '/' + os.path.basename(src)
    else: dst = target

    if os.path.exists(dst):
        if filecmp.cmp(src, dst): return False # Files are the same

        if not force:
            print '\033[91m"%s" already exists.\033[0m' % dst
            return False

    ensure_dir(target)
    shutil.copy(src, target)
    file = target + '/' + os.path.basename(src)
    correct_perms(file)

    return True


def get_extension(filename):
    m = re.match(r'^([^-_]*[-_])*[^-_.]+(?P<ext>\.[^-_]+)$', filename)
    if m: return m.group('ext')
    return ''


def find_builds(src, mode, project, version):
    base = '%s/%s/%s' % (src, mode, project)

    if not os.path.isdir(base): return

    for build in os.listdir(base):
        fullpath = base + '/' + build

        if options.verbose: print 'Checking', fullpath

        if not os.path.isdir(fullpath): continue
        if not re.match(r'^[^-]+-[^-]+-[^-]+$', build): continue
        if not os.path.isdir('%s/v%s' % (fullpath, version)): continue

        yield build


def publish_github(auth, src, project, version):
    user, passwd = auth.split(':')
    builds = list_builds(src, '', project, version)

    releases = {}

    for path, mode, project, build, version in builds:
        p, major, minor, rev = parse_package_version(os.path.basename(path))
        version = '%s.%s.%s' % (major, minor, rev)
        name = '%s-%s-%s' % (project, version, mode)

        if name not in releases:
            releases[name] = {
                'project': project,
                'version': version,
                'mode': mode,
                'paths': []
                }

        releases[name]['paths'].append(path)

    for name, release in releases.items():
        cmd = [
            __dir__ + '/github-release', 'upload', '-c',
            '-u', user,
            '-p', passwd,
            '-r', release['project'],
            '-v', release['version'],
            '-m', release['mode'],
            ] + release['paths']

        subprocess.call(cmd)


def publish_latest(path, target):
    if not options.test:
        if not publish_file(path, target, options.force): return False

        # Link latest
        ext = get_extension(path)
        force_link(os.path.basename(path), '%s/latest%s' % (target, ext))

    print 'Installed %s to %s' % (path, target)

    return True


def list_builds(src, project, version):
    if options.build_mode is not None: modes = [options.build_mode]
    else: modes = ['release', 'debug']

    for mode in modes:
        for build in find_builds(src, mode, project, version):
            base = '%s/%s/%s' % (src, mode, project)
            path = '%s/%s/v%s' % (base, build, version)
            target = [mode, project, build, version]

            if os.path.islink(path + '/latest'): paths = [path + '/latest']
            else: paths = glob.glob(path + '/latest*')

            for latest in paths:
                if not os.path.islink(latest): continue
                latest = os.path.realpath(latest)

                if os.path.isdir(latest):
                    for name in os.listdir(latest):
                        yield [latest + '/' + name] + target
                else: yield [latest] + target


def publish_release(src, dst, project, version):
    for build in list_builds(src, project, version):
        path, mode, project, build, version = build
        target = '%s/%s/%s/%s/v%s' % (dst, mode, project, build, version)
        publish_latest(path, target)


def publish_build(package, slave_name, rev, build):
    filename = os.path.basename(package)
    project, major, minor, rev = parse_package_version(filename)

    slave, mode = parse_slave_name(slave_name)

    project = project.replace('_', '-').lower()
    slave = slave.replace('_', '-').lower()
    mode = mode.lower()

    url = '%s/%s/%s/v%s.%s' % (mode, project, slave, major, minor)
    base = '%s/%s' % (options.builds_dir, url)
    rev_dir = 'r%s-b%s' % (rev, build)
    dir = '%s/%s' % (base, rev_dir)
    url = '%s/%s' % (url, rev_dir)
    latest = '%s/latest' % base

    # Make dir
    ensure_dir(dir)

    # Move
    if options.verbose: print 'mv %s %s' % (package, dir)
    publish_file(package, dir, True)
    os.unlink(package)
    print '%s/%s' % (url, filename)

    # Link latest dir
    if options.verbose: print 'ln -sf %s %s' % (rev_dir, latest)
    force_link(rev_dir, latest)

    # Link latest package
    latest += get_extension(filename)
    latest_package = '%s/%s' % (rev_dir, filename)
    if options.verbose: print 'ln -sf %s %s' % (latest_package, latest)
    force_link(latest_package, latest)

    # Remove old files
    revDirRE = re.compile(r'^r(?P<rev>\d+)-b(?P<build>\d+)$')
    rev_dirs = []
    for name in os.listdir(base):
        m = revDirRE.match(name)
        if m: rev_dirs.append(name)

    if 10 < len(rev_dirs):
        def compare_rev_dirs(x, y):
            m1 = revDirRE.match(x)
            rev1, build1 = m1.groups(['rev', 'build'])
            m2 = revDirRE.match(y)
            rev2, build2 = m2.groups(['rev', 'build'])

            if int(rev1) == int(rev2): return int(build2) - int(build1)
            return int(rev2) - int(rev1)

        rev_dirs = sorted(rev_dirs, cmp = compare_rev_dirs)

        # Delete old revisions
        for dir in rev_dirs[10:]:
            shutil.rmtree(base + '/' + dir, ignore_errors = True)


# Options
default_release_types = 'alpha beta public'

opts = [
    Option('-f', '--force', help = 'Force overwrite', action = 'store_true'),
    Option('-b', '--build', help = 'Build mode, release or debug',
           default = None, dest = 'build_mode', type = 'choice',
           choices = ['release', 'debug']),
    Option('-t', '--test', help = 'Just print what would be done.',
           action = 'store_true'),
    Option('-v', '--verbose', help = 'Verbose output.', action = 'store_true'),
    Option('-g', '--github', help = 'Publish to GitHub',
           metavar = 'USER:TOKEN/PASS'),
    Option('-G', '--group', default = 'www-data',
           help = 'The system group to use when publishing files'),
    Option('-p', '--fperms', default = 0644, type = 'int',
           help = 'The file permissions to use when publishing files'),
    Option('-d', '--dperms', default = 0755, type = 'int',
           help = 'The directory permissions to use when publishing files'),
    Option('--builds-dir', default = './builds',
           help = 'The directory in which to publish builds'),
    Option('--releases-dir', default = './releases',
           help = 'The directory in which to publish releases'),
    Option('--release-types', default = default_release_types,
           help = 'Releases are organized in to directories of these types')
]

usage = 'Usage: %prog [OPTIONS] [COMMAND] <args>...'

epilog = '''
Commands:
  release <project> <version> <release>
      project      The name of the project being released.
      version      The two digit version number in <major>.<minor> format.
      release      One of: %s

  build <package> <slave name> <revision> <build>
      package      The filename of the package being released.
      slave name   The name of the build slave.
      revision     The repository revision number.
      build        The build number.
''' % default_release_types



class OptParser(OptionParser):
    def format_epilog(self, formatter):
        return self.epilog


    def error(self, msg):
        self.print_help()
        print '\n\nUsage error: %s' % msg
        sys.exit(1)


def run():
    # Parse command line
    parser = OptParser(option_list = opts, usage = usage, epilog = epilog)
    options, args = parser.parse_args()

    # Get commmand
    if len(args) < 1: parser.error('Missing command')
    cmd = args[0]
    args = args[1:]

    # Run command
    if cmd == 'release':
        if len(args) != 3: parser.error('Missing positional arguments')

        project, version, release = args
        project = project.lower()

        if not re.match(r'^\d+\.\d+$', version):
            parser.error('Invalid version "%s".  Must be <major>.<minor>' % \
                             version)

        if release not in options.release_types.split():
            parser.error('Invalid release mode "%s"' % release)

        src = options.builds_dir
        dst = options.releases_dir + '/' + release

        if options.github: publish_github(options.github, dst, project, version)
        else: publish_release(src, dst, project, version)

    elif cmd == 'build':
        if len(args) != 4: parser.error('Missing positional arguments')
        publish_build(*args)


if __name__ == "__main__": run()
