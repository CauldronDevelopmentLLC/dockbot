import shutil
import os
import dockbot
import requests


class RemoteSlave(dockbot.Slave):
    def kind(self): return 'Remote Slave'
    def get_status(self): return dockbot.REMOTE
    def is_running(self): return False
    def exists(self): return True
    def cmd_delete(self): self.cmd_status()
    def cmd_status(self): dockbot.status_line(self.qname, *dockbot.REMOTE)
    def cmd_shell(self): self.cmd_status()
    def cmd_start(self, shell = False): self.cmd_status()
    def prepare_start(self): raise dockbot.Error('Cannot start remote slave')
    def cmd_stop(self): self.cmd_status()
    def cmd_restart(self): self.cmd_status()
    def cmd_build(self): self.cmd_status()
