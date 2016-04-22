import shutil
import os
import dockbot
import requests


class Slave(dockbot.Container):
    def kind(self): return 'Slave'


    def cmd_trigger(self, project = 'all'):
        if dockbot.args.all and not self.is_running():
            self.cmd_start()

        if not self.is_running():
            raise dockbot.Error('Slave container not running')

        if project != 'all' and project not in self.image.projects:
            raise dockbot.Error('Unknown project %s' % project)

        url = 'http://%s:%d/builders/%s-%s/force' % (
            self.conf['ip'], int(self.conf['http-port']),
            self.name, project)

        if dockbot.args.verbose: print 'triggering', url

        r = requests.get(url)
        if r.status_code != 200:
            msg = 'Failed to trigger build, possibly an HTTP proxy problem.'
            if dockbot.args.verbose: msg += '\n' + r.text
            raise dockbot.Error(msg)



    def prepare_start(self):
        # Prepare run directory
        dockbot.mkdirs(self.run_dir + '/' + self.name)
        info_dir = self.run_dir + '/info'
        dockbot.mkdirs(info_dir)
        dockbot.touch(info_dir + '/host')
        open(info_dir + '/admin', 'w').write(self.conf['admin'] + '\n')

        # Install slave.tac
        path = dockbot.get_resource('data/slave.tac')
        dockbot.publish_file(path, self.run_dir)

        # Install scons options
        f = None
        try:
            f = open(self.run_dir + '/' + 'scons_options.py', 'w', 0644)

            for key, value in self.scons.items():
                f.write('%s = %s\n' % (key, value.__repr__()))

        finally:
            if f is not None: f.close()

        # Environment
        cmd = ['-e', 'SCONS_OPTIONS=/host/scons_options.py',
               '-e', 'PLATFORM=' + self.image.platform,
               '-e', 'DOCKBOT_NAMESPACE=' + self.conf['namespace']]

        # Link to buildmaster
        cmd += ['--link', '%s-buildmaster:buildmaster' % self.conf['namespace']]

        return cmd
