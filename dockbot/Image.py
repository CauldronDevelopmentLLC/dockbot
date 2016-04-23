import shutil
import os
import hashlib
import dockbot


def gen_hash(data):
    return hashlib.sha256(data).hexdigest()


class Image(object):
    def __init__(self, root, name, path, platform = None, projects = [],
                 modes = None, slave = False):
        self.root = root
        self.conf = root.conf
        self.name = name
        self.qname = self.conf['namespace'] + '-' + name
        self.path = path
        self.dir = os.path.dirname(path)
        self.platform = platform
        self.projects = projects
        self.modes = modes
        self.context = self.conf.get_list('context', platform, slave)

        self.containers = []
        if slave:
            for mode in modes:
                self.containers.append(dockbot.Slave(self, mode))
        else:
            self.context += [
                dockbot.get_resource('dockbot/data/master/nginx.conf')]
            self.containers.append(dockbot.Master(self))

        self.deps = set()
        for project in self.projects:
            self.deps.update(self.conf.get_project_deps(project))


    def __eq__(self, other): return self.name == other.name
    def __ne__(self, other): return not self.__eq__(other)

    def kind(self): return 'Image'


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

        if ret: raise dockbot.Error('Failed to construct Docker file: ' + err)

        return out


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
            raise dockbot.Error('Cannot rebuild image while any of its '
                                'containers are running')

        # Delete image if it exists
        self.cmd_delete()

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
            f.write(data)
            f.close()

            f = open(self.get_hash_path(), 'w')
            f.write(data_hash)

        finally:
            if f is not None: f.close()

        # Link context
        for path in self.context:
            target = os.path.join(ctx_path, os.path.basename(path))
            if dockbot.args.verbose: print '%s -> %s' % (path, target)
            shutil.copy(path, target)

        # Build command
        cmd = ['docker', 'build', '--rm', '-t', self.qname]

        # Extra args
        cmd += dockbot.args.args

        # Do build
        dockbot.system(cmd + ['.'], False, 'build image', cwd = ctx_path)


    def cmd_trigger(self):
        for container in self.containers:
            if isinstance(container, dockbot.Slave):
                container.cmd_trigger()
