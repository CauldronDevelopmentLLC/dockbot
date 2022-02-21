import shutil
import os
import dockbot
import json


class RemoteSlave(dockbot.Slave):
    def kind(self): return 'Remote Slave'
    def get_status(self): return dockbot.REMOTE
    def is_running(self): return False
    def exists(self): return True
    def cmd_delete(self): self.cmd_status()
    def cmd_status(self): dockbot.status_line(self.qname, *dockbot.REMOTE)
    def cmd_shell(self): self.cmd_status()
    def cmd_start(self, shell = False): self.cmd_status()


    def cmd_build(self):
        dockbot.status_line(self.qname, *dockbot.BUILDING)

        self.prepare_start()

        # Copy scripts
        path = dockbot.get_resource('dockbot/data/bin')
        dockbot.copy_tree(path, self.run_dir + '/bin')

        # Copy context
        dockbot.copy_tree(self.image.dir, self.run_dir)

        # Write env.json
        env = {
            'SLAVE_NAME': self.name,
            'SLAVE_PASS': self.conf['passwd'],
            'DOCKBOT_MASTER_PORT': self.conf['buildbot-port'],
            'DOCKBOT_MASTER_HOST': self.conf['host'],
            'SCONS_OPTIONS': '$PWD/scons_options.py',
            'PLATFORM': self.image.platform,
            'PATH': ['$PWD/bin', '$PATH'],
            }
        env.update(self.env)

        self.write_env(env)
