import shutil
import os
import hashlib
import dockbot


def gen_hash(data):
    return hashlib.sha256(data).hexdigest()


class Image(object):
    def __init__(self, root, name, path, platform = None, projects = [],
                 modes = None, slave = False, remote = False):
        self.root = root
        self.conf = root.conf
        self.name = name
        self.qname = self.conf['namespace'] + '-' + name
        self.platform = platform
        self.modes = modes

        if not remote:
            self.path = path
            self.dir = os.path.dirname(path)
            self.context = self.conf.get_list('context', platform, slave)

        self.containers = []
        if not slave:
            self.context += [
                dockbot.get_resource('dockbot/data/master/nginx.conf')]
            self.containers.append(dockbot.Master(self))
            return

        # Slave only from here
        for mode in modes:
            self.containers.append(self.create_slave(mode))

        # Slave projects
        self.projects = set()
        for project in projects:
            self.projects.update(self.conf.get_project_deps(project))

        # Get project overrides
        self.project_overrides = \
            self.conf.get_sub_key(platform).get('projects', {})


    def __eq__(self, other): return self.name == other.name
    def __ne__(self, other): return not self.__eq__(other)

    def kind(self): return 'Image'


    def create_slave(self, mode): return dockbot.Slave(self, mode)


    def is_running(self):
        for container in self.containers:
            if container.is_running(): return True
        return False


    def get_context_path(self):
        return 'run/docker/' + self.name


    def get_hash_path(self):
        return self.get_context_path() + '.sha256'


    def get_data_hash(self):
        path = self.get_hash_path()

        if os.path.exists(path):
            f = None
            try:
                f = open(path, 'rt')
                return f.read()
            finally:
                if f is not None: f.close()


    def is_dirty(self):
        if dockbot.args.force: return False
        return self.get_data_hash() != gen_hash(self.gen_dockerfile())


    def gen_dockerfile(self):
        libpath = [os.path.dirname(self.path)]
        libpath += self.conf.get('libpath', ['lib'])
        libpath += [dockbot.get_resource('dockbot/data/lib')]

        cmd = ['m4'] + sum([['-I', x] for x in libpath], []) + [self.path]
        ret, out, err = dockbot.system(cmd, True)

        if ret:
            raise dockbot.Error('Failed to construct Docker file: ' +
                                err.decode('utf-8'))

        return out


    def get_project(self, name):
        import copy
        for project in self.conf.projects:
            if project['name'] == name:
                p = copy.deepcopy(project)
                p.update(self.project_overrides.get(name, {}))
                return p

        raise dockbot.Error('Project "%s" not found' % name)


    def exists(self):
        return dockbot.inspect(self.qname) != dockbot.NOT_FOUND


    def cmd_delete(self):
        if self.exists():
            for container in self.containers:
                container.cmd_delete()

            dockbot.status_line(self.qname, *dockbot.DELETING)
            dockbot.system(['docker', 'rmi', '--no-prune', self.qname], True,
                           'remove image')


    def container_exists(self):
        for container in self.containers:
            if container.exists(): return True
        return False


    def cmd_status(self):
        for container in self.containers:
            container.cmd_status()


    def cmd_config(self):
        for container in self.containers:
            container.cmd_config()


    def cmd_shell(self):
        raise dockbot.Error('Cannot open shell in image')


    def cmd_start(self):
        for container in self.containers:
            container.cmd_start()


    def cmd_stop(self):
        for container in self.containers:
            container.cmd_stop()


    def cmd_restart(self):
        self.cmd_stop()
        self.cmd_start()


    def cmd_build(self):
        # Check if image is running
        if self.is_running():
            if dockbot.args.all and (self.is_dirty() or dockbot.args.force):
                self.cmd_stop()
            else:
                dockbot.status_line(self.qname, *dockbot.RUNNING)
                return

        if self.is_dirty() or dockbot.args.force:
            self.cmd_delete() # Delete image if it exists

        elif self.exists():
            dockbot.status_line(self.qname, *dockbot.BUILT)
            return

        dockbot.status_line(self.qname, *dockbot.BUILDING)

        # Generate Dockerfile
        data = self.gen_dockerfile()
        data_hash = gen_hash(data)

        # Clean up old context
        ctx_path = self.get_context_path()
        if os.path.exists(ctx_path): shutil.rmtree(ctx_path)

        # Construct Dockerfile
        os.makedirs(ctx_path)
        dockerfile = ctx_path + '/Dockerfile'

        f = None
        try:
            f = open(dockerfile, 'w')
            f.write(data.decode('utf-8'))
            f.close()

            f = open(self.get_hash_path(), 'w')
            f.write(data_hash)

        finally:
            if f is not None: f.close()

        # Link context
        for path in self.context:
            target = os.path.join(ctx_path, os.path.basename(path))
            if dockbot.args.verbose: print('%s -> %s' % (path, target))
            shutil.copy(path, target)

        # Build command
        cmd = ['docker', 'build', '--rm', '-t', self.qname]

        # Extra args
        cmd += dockbot.args.args

        # Do build
        dockbot.system(cmd + ['.'], False, 'build ' + self.qname,
                       cwd = ctx_path)


    def cmd_trigger(self):
        for container in self.containers:
            if isinstance(container, dockbot.Slave):
                container.cmd_trigger()


    def cmd_publish(self):
        for container in self.containers:
            container.cmd_publish()
