import shutil
import os
import dockbot
import re
import glob
import shutil
import filecmp
import subprocess
import getpass
import pipes


def find_newest_version(path):
    versions = []

    for version in os.listdir(path):
        if re.match(r'v\d+\.\d+', version):
            versions.append(map(int, version[1:].split('.')))

    versions = sorted(versions, reverse = True)
    if len(versions): return '%d.%d' % tuple(versions[0])


def list_builds(path):
    if os.path.islink(path + '/latest'): paths = [path + '/latest']
    else: paths = glob.glob(path + '/latest*')

    for latest in paths:
        if not os.path.islink(latest): continue
        latest = os.path.realpath(latest)

        if latest.startswith(os.getcwd()):
            latest = '.' + latest[len(os.getcwd()):]

        if os.path.isdir(latest):
            for name in os.listdir(latest):
                yield latest + '/' + name
        else: yield latest


def correct_perms(path):
    if os.path.isdir(path): os.chmod(path, dockbot.args.dperms)
    else: os.chmod(path, dockbot.args.fperms)
    if dockbot.args.group:
        os.lchown(path, -1, grp.getgrnam(dockbot.args.group)[2])


def ensure_dir(path):
    if os.path.exists(path): return

    # Make sure parent exists
    parent, child = os.path.split(os.path.normpath(path))
    if parent and parent != path: ensure_dir(parent)

    # Create directory with correct permissions and group
    os.mkdir(path, dockbot.args.dperms)
    if dockbot.args.group:
        os.lchown(path, -1, grp.getgrnam(dockbot.args.group)[2])


def force_link(src, dst):
    if os.path.islink(dst): os.remove(dst)
    os.symlink(src, dst)
    correct_perms(dst)


def publish_file(src, target, install):
    if os.path.isdir(target): dst = target + '/' + os.path.basename(src)
    else: dst = target

    if not dockbot.args.force and os.path.exists(dst):
        if filecmp.cmp(src, dst): return False # Files are the same
        print '\033[91m"%s" already exists.\033[0m' % dst
        return False

    ensure_dir(target)
    install(src, target)
    correct_perms(dst)

    return True


def get_extension(filename):
    m = re.match(r'^([^-_]*[-_])*[^-_.]+(?P<ext>\.[^-_]+)$', filename)
    if m: return m.group('ext')
    return ''


def publish_latest(src, target, install = shutil.copy):
    if not publish_file(src, target, install): return

    # Link latest
    ext = get_extension(src)
    force_link(os.path.basename(src), '%s/latest%s' % (target, ext))

    print 'Installed %s to %s' % (src, target)


def osslsigncode(src, target, summary = None, url = None):
    if not dockbot.args.key: raise dockbot.Error('Missing --key <path>')

    while not dockbot.args.password:
        dockbot.args.password = getpass.getpass('Key password: ')

    cmd = ['osslsigncode', 'sign', '-pkcs12', dockbot.args.key, '-in', src,
           '-out', target + '/' + os.path.basename(src)]

    if summary: cmd += ['-n', summary]
    if url: cmd += ['-i', url]
    if dockbot.args.ts_url: cmd += ['-ts', dockbot.args.ts_url]

    if dockbot.args.verbose:
        print 'Calling:', ' '.join(pipes.quote(s) for s in cmd)

    cmd += ['-pass', dockbot.args.password]

    if subprocess.call(cmd): raise dockbot.Error('Code signing failed')



class Slave(dockbot.Container):
    def kind(self): return 'Slave'


    def cmd_trigger(self):
        if dockbot.args.project is None: project = 'all'
        else: project = dockbot.args.project

        if not isinstance(self, dockbot.RemoteSlave):
            if dockbot.args.all and not self.is_running():
                self.cmd_start()

            if not self.is_running():
                dockbot.status_line(self.qname, *self.get_status())
                return

        if project != 'all' and project not in self.image.projects:
            raise dockbot.Error('Unknown project %s' % project)

        dockbot.trigger(self.name, project, self.conf)


    def cmd_publish(self):
        if dockbot.args.project is None: projects = self.image.projects
        else: project = [dockbot.args.project]

        if dockbot.args.mode is not None and dockbot.args.mode != self.mode:
            return

        for project in projects:
            path = 'run/buildmaster/builds/%s/%s/%s' % (
                self.mode, project, self.image.platform.lower())
            target = './releases/%s/%s/%s/%s' % (
                dockbot.args.release, self.mode, project,
                self.image.platform.lower())
            p = self.image.get_project(project)

            if os.path.isdir(path):
                if dockbot.args.version is None:
                    version = find_newest_version(path)
                    if not version: continue
                else: version = dockbot.args.version

                path += '/v' + version
                target += '/v' + version

                for build in list_builds(path):
                    if 'sign' in p:
                        def install(src, target):
                            osslsigncode(src, target, p.get('summary', None),
                                         self.conf.get('url', None))

                        publish_latest(build, target, install)

                    else: publish_latest(build, target)


    def prepare_start(self):
        # Prepare run directory
        dockbot.mkdirs(self.run_dir + '/' + self.name)
        info_dir = self.run_dir + '/info'
        dockbot.mkdirs(info_dir)
        dockbot.touch(info_dir + '/host')
        open(info_dir + '/admin', 'w').write(self.conf['admin'] + '\n')

        # Install slave.tac
        path = dockbot.get_resource('dockbot/data/slave.tac')
        dockbot.publish_file(path, self.run_dir)
        os.chmod(self.run_dir + '/slave.tac', 0755)

        # Install scons options
        f = None
        try:
            f = open(self.run_dir + '/' + 'scons_options.py', 'w', 0644)

            for key, value in self.scons.items():
                f.write('%s = %s\n' % (key, value.__repr__()))

        finally:
            if f is not None: f.close()

        # Environment
        env = {
            'DOCKBOT_MASTER_HOST': '%(namespace)s-buildmaster' % self.conf,
            'DOCKBOT_MASTER_PORT': 9989,
            'SCONS_OPTIONS': '$PWD/scons_options.py',
            }

        # Link to buildmaster
        cmd = ['--link', '%(namespace)s-buildmaster:buildmaster' % self.conf]

        return cmd, env
