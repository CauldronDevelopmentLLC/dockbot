import json
import re
import os
import dockbot


class Container(object):
    def __init__(self, image, mode = None):
        self.image = image
        self.mode = mode
        self.conf = image.conf

        self.name = image.name
        if mode is not None: self.name += '-' + mode
        self.qname = self.conf['namespace'] + '-' + self.name

        slave = True if mode is not None else False
        self.env = self.conf.get_dict('env', image.platform, slave, mode)
        self.scons = self.conf.get_dict('scons', image.platform, slave, mode)
        self.args = self.conf.get_list('args', image.platform, slave, mode)
        self.ports = self.conf.get_list('ports', image.platform, slave, mode)

        self.run_dir = 'run/' + self.name


    def get_status(self):
        data = dockbot.inspect(self.qname)
        if data == dockbot.NOT_FOUND or 'State' not in data[0]:
            if self.image.exists():
                if self.image.is_dirty(): return dockbot.DIRTY
                else: return dockbot.BUILT
            else: return dockbot.NOT_FOUND

        if data[0]['State']['Running']: return dockbot.RUNNING
        elif self.image.is_dirty(): return dockbot.DIRTY
        else: return dockbot.OFFLINE


    def get_slave_root(self):
        conf = self.conf[self.image.platform]

        if 'modes' in conf and self.mode in conf['modes'] and \
                'root' in conf['modes'][self.mode]:
            return conf['modes'][self.mode]['root']

        if 'root' in conf: return conf['root'] + '/' + self.name

        return '/host'


    def is_running(self):
        return self.get_status() == dockbot.RUNNING


    def exists(self):
        data = dockbot.inspect(self.qname)
        return data != dockbot.NOT_FOUND and 'State' in data[0]


    def write_env(self, env):
        f = open(self.run_dir + '/env.json', 'w')
        json.dump(env, f, ensure_ascii = False, sort_keys = True, indent = 2,
                  separators = (',', ': '))
        f.close()


    def cmd_delete(self):
        if self.is_running():
            if dockbot.args.all: self.cmd_stop()
            else:
                dockbot.status_line(self.qname, *dockbot.RUNNING)
                return

        if self.exists():
            dockbot.system(['docker', 'rm', self.qname], True,
                           'delete container')


    def cmd_status(self):
        dockbot.status_line(self.qname, *self.get_status())


    def cmd_config(self):
        config = {'env': self.env, 'scons': self.scons, 'args': self.args,
                  'ports': self.ports, 'run_dir': self.run_dir}
        print json.dumps(config, indent = 4, separators = (',', ': '))


    def cmd_shell(self):
        if self.is_running():
            dockbot.system(['docker', 'exec', '-it', self.qname, 'bash'])

        else: self.cmd_start(True)


    def cmd_start(self, shell = False):
        if self.is_running():
            dockbot.status_line(self.qname, *dockbot.RUNNING)
            return

        if (not self.image.exists() or self.image.is_dirty()) and \
                dockbot.args.all: self.cmd_build()

        if not self.image.exists():
            dockbot.status_line(self.qname, *dockbot.NOT_FOUND)
            return

        if self.image.is_dirty():
            dockbot.status_line(self.qname, *dockbot.DIRTY)
            return

        self.cmd_delete()

        dockbot.status_line(self.qname, *dockbot.STARTING)

        # Create run dir
        dockbot.mkdirs(self.run_dir)

        # Copy scripts
        path = dockbot.get_resource('dockbot/data/bin')
        dockbot.copy_tree(path, self.run_dir + '/bin')

        # Copy context
        dockbot.copy_tree(self.image.dir, self.run_dir)

        # Setup command
        cmd = ['docker', 'run', '--name', self.qname,
               '-v', '%s/%s:/host' % (os.getcwd(), self.run_dir)]

        env = {}
        if not shell:
            _cmd, _env = self.prepare_start()
            cmd += _cmd
            env.update(_env)

        # Environment
        env.update({
                'SLAVE_NAME': self.name,
                'SLAVE_PASS': self.conf['passwd'],
                'PLATFORM': self.image.platform,
                })
        env.update(self.env)
        self.write_env(env)

        # Ports
        for port in self.ports: cmd += ['-p', port]

        # Foreground
        if dockbot.args.foreground or shell: cmd += ['-it']
        else: cmd += ['-d']

        # Shell
        if shell: cmd += ['--entrypoint', '/bin/bash']

        # Extra args
        cmd += self.args + dockbot.args.args

        # Image
        cmd.append(self.image.qname)

        # Run it
        if shell: dockbot.system(cmd)
        else: dockbot.system(cmd, False, 'start container')


    def prepare_start(self):
        raise Exception('Not implemented')


    def cmd_stop(self):
        if self.is_running():
            dockbot.status_line(self.qname, *dockbot.STOPPING)
            dockbot.system(['docker', 'stop', self.qname], True,
                           'stop container')


    def cmd_restart(self):
        self.cmd_stop()
        self.cmd_start()


    def cmd_build(self):
        self.image.cmd_build()


    def cmd_publish(self): pass
