import json
import os
import sys
import random
import string
import fnmatch
import dockbot


def gen_password():
    if os.path.exists('passwd'): return open('passwd', 'r').read()

    chars = string.ascii_letters + string.digits
    random.seed = os.urandom(1024)
    passwd = ''.join(random.choice(chars) for i in range(16))

    f = None
    try:
        f = open('passwd', 'w')
        f.write(passwd)

    finally:
        if f is not None: f.close()

    return passwd


def command(args, instance):
    try:
        func = getattr(instance, 'cmd_' + args.cmd)
    except AttributeError:
        raise dockbot.Error('Invalid command "%s" for %s.' % (
                args.cmd, instance.kind()))

    func()


def set_default(d, name, value):
    if not name in d: d[name] = value



class Dockbot(object):
    def __init__(self, args):
        if not os.path.exists('dockbot.json'):
            raise dockbot.Error(
                'ERROR: `dockbot.json` not found in the current directory.\n'
                'Must be run in the top-level directory of a dockbot '
                'configuration.')

        try:
            conf = json.load(open('dockbot.json', 'r'))
            if os.path.exists('dockbot.local'):
                conf.update(json.load(open('dockbot.local', 'r')))

            self.conf = dockbot.Config(conf)
            self.conf['project']
            self.conf['url']
            self.conf['namespace']
            self.conf['modes']
            self.conf['admin']

        except Exception, e:
            raise dockbot.Error('%s\n\nFailed to parse `dockbot.json`' % e)

        # Defaults
        set_default(self.conf, 'ip', '127.0.0.1')
        set_default(self.conf, 'http-port', 8080)

        # Master
        dockerfile = dockbot.get_resource('dockbot/data/master/master.docker')
        master = dockbot.Image(self, 'buildmaster', dockerfile)

        # Find slaves
        self.slaves = list(self.load_slaves(args.slaves))
        self.images = [master] + self.slaves

        if 'passwd' not in self.conf:
            self.conf['passwd'] = gen_password()

        # Run command in single image/container or all
        if args.name is None: targets = self.images
        elif args.name == 'master': targets = [master]
        else:
            targets = self.find_instances(args.name)
            if not targets:
                raise dockbot.Error('Invalid image or container "%s"' %
                                   args.name)

        for target in targets:
            try:
                command(args, target)

            except dockbot.Error, e:
                print '\n%s\n' % e
                if not args._continue: sys.exit(1)


    def load_slaves(self, slave_root):
        for slave in os.listdir(slave_root):
            slave_dir = os.path.join(slave_root, slave)
            conf_path = slave_dir + '/dockbot.json'

            if os.path.exists(conf_path):
                slave_conf = json.load(open(conf_path, 'r'))
                self.conf[slave] = slave_conf
                remote = slave_conf.get('remote', False)
                modes = self.conf['modes'].keys()

                for name, data in slave_conf.get('images', {}).items():
                    fullname = ('%s-%s' % (slave, name)).lower()
                    projects = data.get('projects', [])
                    image_modes = data.get('modes', modes)

                    if remote:
                        yield dockbot.RemoteImage(self, fullname, slave_dir,
                                                  slave, projects, image_modes)

                    else:
                        dockerfile = '%s/%s.docker' % (slave_dir, name)
                        if not os.path.exists(dockerfile):
                            raise dockbot.Error('Missing file %s' % dockerfile)

                        yield dockbot.Image(self, fullname, dockerfile, slave,
                                            projects, image_modes, True)


    def find_instances(self, pattern):
        instances = []

        for image in self.images:
            for container in image.containers:
                if fnmatch.fnmatch(container.qname, pattern):
                    instances.append(container)

        if not instances:
            for image in self.images:
                if fnmatch.fnmatch(image.qname, pattern):
                    instances.append(image)

        return instances
