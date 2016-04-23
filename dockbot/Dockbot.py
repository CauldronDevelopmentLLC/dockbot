import json
import os
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

    if args.project: func(args.project)
    else: func()



class Dockbot(object):
    def __init__(self, args, conf_file):
        try:
            self.conf = dockbot.Config(json.load(open(conf_file, 'r')))
            self.conf['project']
            self.conf['url']
            self.conf['namespace']
            self.conf['modes']
            self.conf['admin']
            self.conf['ip']

        except Exception, e:
            raise dockbot.Error('%s\n\nFailed to parse config file "%s"' % (
                    e, conf_file))

        # Master
        dockerfile = dockbot.get_resource('dockbot/data/master/master.docker')
        master = dockbot.Image(self, 'buildmaster', dockerfile)

        # Find slaves
        self.slaves = list(self.load_slaves(args.slaves))
        self.images = [master] + self.slaves

        if 'passwd' not in self.conf:
            self.conf['passwd'] = gen_password()

        # Run command in single image/container or all
        if args.name is None: map(lambda x: command(args, x), self.images)
        elif args.name == 'master': command(args, master)
        else:
            instances = self.find_instances(args.name)
            if not instances:
                raise dockbot.Error('Invalid image or container "%s"' %
                                   args.name)

            map(lambda x: command(args, x), instances)


    def load_slaves(self, slave_root):
        for slave in os.listdir(slave_root):
            slave_dir = os.path.join(slave_root, slave)
            conf_path = slave_dir + '/dockbot.json'

            if os.path.exists(conf_path):
                slave_conf = json.load(open(conf_path, 'r'))
                self.conf[slave] = slave_conf

                for name, data in slave_conf.get('images', {}).items():
                    dockerfile = '%s/%s.docker' % (slave_dir, name)
                    if not os.path.exists(dockerfile):
                        raise dockbot.Error('Missing file %s' % dockerfile)

                    name = ('%s-%s' % (slave, name)).lower()
                    projects = data.get('projects', [])
                    image_modes = data.get('modes', self.conf['modes'])

                    yield dockbot.Image(self, name, dockerfile, slave,
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
