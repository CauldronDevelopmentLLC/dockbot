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
            if self.image.exists(): return dockbot.BUILT
            else: return dockbot.NOT_FOUND

        if data[0]['State']['Running']: return dockbot.RUNNING
        else: return dockbot.OFFLINE


    def is_running(self):
        return self.get_status() == dockbot.RUNNING


    def exists(self):
        data = dockbot.inspect(self.qname)
        return data != dockbot.NOT_FOUND and 'State' in data[0]


    def delete(self):
        if self.exists():
            dockbot.system(['docker', 'rm', self.qname], True,
                           'delete container')


    def status(self):
        dockbot.status_line(self.qname, *self.get_status())


    def config(self):
        config = {'env': self.env, 'scons': self.scons, 'args': self.args,
                  'ports': self.ports, 'run_dir': self.run_dir}
        print json.dumps(config, indent = 4, separators = (',', ': '))


    def shell(self):
        if self.is_running():
            dockbot.system(['docker', 'exec', '-it', self.qname, 'bash'])
        else: self.start(True)


    def start(self, shell = False):
        if self.is_running(): return
        if not self.image.exists(): return
        self.delete()

        dockbot.status_line(self.qname, *dockbot.STARTING)

        # Create run dir
        dockbot.mkdirs(self.run_dir)

        # Copy context
        for root, subdirs, files in os.walk(self.image.dir):
            target_dir = re.sub(r'^' + self.image.dir, self.run_dir, root)
            dockbot.mkdirs(target_dir)

            for filename in files:
                dockbot.publish_file(root + '/' + filename, target_dir)

        # Setup command
        cmd = ['docker', 'run', '--name', self.qname,
               '-v', '%s/%s:/host' % (os.getcwd(), self.run_dir)]

        cmd += self.prepare_start()

        # Environment
        cmd += ['-e', 'CONTAINER_NAME=' + self.name,
                '-e', 'SLAVE_PASS=' + self.conf['passwd']]
        for key, value in self.env.items():
            cmd += ['-e', '%s=%s' % (key, value)]

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


    def stop(self):
        if self.is_running():
            dockbot.status_line(self.qname, *dockbot.STOPPING)
            dockbot.system(['docker', 'stop', self.qname], True,
                           'stop container')


    def restart(self):
        self.stop()
        self.start()


    def build(self):
        self.image.build()


    def rebuild(self):
        self.image.rebuild()
