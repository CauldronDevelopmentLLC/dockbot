import shutil
import os
import dockbot


class RemoteImage(dockbot.Image):
    def __init__(self, root, name, dir, platform = None, projects = [],
                 modes = None, slave = True, remote = True):
        self.dir = dir
        dockbot.Image.__init__(self, root, name, None, platform, projects,
                               modes, slave, remote)

    def kind(self): return 'Remote Image'
    def create_slave(self, mode): return dockbot.RemoteSlave(self, mode)
    def is_dirty(self): return False
    def exists(self): return True
    def cmd_delete(self): self.cmd_status()
    def cmd_shell(self): self.cmd_status()
    def cmd_start(self): self.cmd_status()


    def cmd_build(self):
        for container in self.containers:
            container.cmd_build()
