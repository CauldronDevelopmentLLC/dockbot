import json
import os
import random
import string
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


def call(cmd, instance):
    try:
        getattr(instance, cmd)()
    except AttributeError:
        raise dockbot.Error('Invalid command "%s"' % cmd)



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
        dockerfile = dockbot.get_resource('data/master/master.docker')
        master = dockbot.Image(self, 'buildmaster', dockerfile)

        # Find slaves
        self.slaves = list(self.load_slaves(args.slaves))
        self.images = [master] + self.slaves

        if 'passwd' not in self.conf:
            self.conf['passwd'] = gen_password()

        # Run command in single image/container or all
        if args.name is None: map(lambda x: call(args.cmd, x), self.images)
        elif args.name == 'master': call(args.cmd, master)
        else:
            instance = self.find_instance(args.name)
            if instance is None:
                raise dockbot.Error('Invalid image or container "%s"' %
                                   args.name)

            call(args.cmd, instance)


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


    def walk_instances(self):
        for image in self.images:
            yield image
            for container in image.containers:
                yield container


    def find_instance(self, name):
        for instance in self.walk_instances():
            if instance.qname == name: return instance
