import shutil
import os
import dockbot


class RemoteImage(dockbot.Image):
    def __init__(self, root, name, platform = None, projects = [],
                 modes = None):
        self.root = root
        self.conf = root.conf
        self.name = name
        self.qname = self.conf['namespace'] + '-' + name
        self.platform = platform
        self.modes = modes

        self.containers = []
        for mode in modes:
            self.containers.append(dockbot.RemoteSlave(self, mode))

        self.projects = set()
        for project in projects:
            self.projects.update(self.conf.get_project_deps(project))


    def kind(self): return 'Remote Image'
    def is_dirty(self): return False
    def exists(self): return True
    def cmd_delete(self): self.cmd_status()
    def cmd_shell(self): self.cmd_status()
    def cmd_start(self): self.cmd_status()
    def cmd_stop(self): self.cmd_status()
    def cmd_restart(self): self.cmd_status()
    def cmd_build(self): self.cmd_status()
