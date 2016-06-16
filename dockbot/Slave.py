import shutil
import os
import dockbot


class Slave(dockbot.Container):
    def kind(self): return 'Slave'


    def cmd_trigger(self):
        if dockbot.args.project is None: project = 'all'
        else: project = dockbot.args.project

        if dockbot.args.all and not self.is_running():
            self.cmd_start()

        if not self.is_running():
            dockbot.status_line(self.qname, *self.get_status())
            return

        if project != 'all' and project not in self.image.projects:
            raise dockbot.Error('Unknown project %s' % project)

        dockbot.trigger(self.name, project, self.conf)


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
        cmd = ['-e', 'SCONS_OPTIONS=/host/scons_options.py',
               '-e', 'PLATFORM=' + self.image.platform,
               '-e',
               'DOCKBOT_MASTER_HOST=%(namespace)s-buildmaster' % self.conf,
               '-e', 'DOCKBOT_MASTER_PORT=9989']

        # Link to buildmaster
        cmd += ['--link', '%(namespace)s-buildmaster:buildmaster' % self.conf]

        return cmd
