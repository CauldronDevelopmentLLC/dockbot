import shutil
import os
import dockbot


class Slave(dockbot.Container):
    def prepare_start(self):
        # Prepare run directory
        dockbot.mkdirs(self.run_dir + '/' + self.name)
        info_dir = self.run_dir + '/info'
        dockbot.mkdirs(info_dir)
        dockbot.touch(info_dir + '/host')
        open(info_dir + '/admin', 'w').write(self.conf['admin'] + '\n')

        if not os.path.exists(self.run_dir + '/slave.tac'):
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
               '-e', 'PLATFORM=' + self.image.platform]

        # Link to buildmaster
        cmd += ['--link', '%s-buildmaster:buildmaster' % self.conf['namespace']]

        return cmd
