import os
import copy
import dockbot


local_cfg_hdr = '''\
# -*- python -*-
# Autogenerated file

c['projectName'] = '%(project)s'
c['projectURL'] = '%(url)s'
c['debugPassword'] = '%(passwd)s'
'''


class Master(dockbot.Container):
    def kind(self): return 'Master'


    def gen_config(self):
        f = None
        try:
            f = open('run/%s/local.cfg' % self.name, 'w')
            f.write(local_cfg_hdr % self.conf)

            # Gather project deps
            projects = {}
            for p in self.conf.projects: projects.update({p['name']: p})

            def project_deps(name):
                project = projects[name]
                yield name

                for dep in project.get('deps', []):
                    for x in project_deps(dep):
                        yield x

            for project in projects.values():
                project['full_deps'] = set(project_deps(project['name']))

            # Gather project slaves
            project_slaves = {}
            for slave in self.image.root.slaves:
                for project in slave.projects:
                    if project not in project_slaves:
                        project_slaves[project] = set()

                    for container in slave.containers:
                        project_slaves[project].add(container)

            # Sort projects
            project_order = []
            project_visited = set()
            def order_projects(name):
                if name in project_visited: return
                project_visited.add(name)
                project = projects[name]

                for dep in project.get('deps', []):
                    order_projects(dep)

                project_order.append(project)

            for name in projects.keys(): order_projects(name)

            # Slaves
            f.write('\n# Slaves\n')
            for slave in self.image.root.slaves:
                for container in slave.containers:
                    args = {
                        'name': container.name,
                        'password': self.conf['passwd'],
                        'types': [],
                        'root': container.get_slave_root()
                        }

                    f.write('add_slave(**%s)\n' % args.__repr__())

            # Repos
            f.write('\n# Repos\n')
            for project in project_order:
                f.write('c["repo"]["%s"] = %s\n' % (
                        project['name'], project['repo'].__repr__()))

            # Projects
            f.write('\n# Projects\n')
            for project in project_order:
                name = project['name']

                for slave in project_slaves.get(name, []):
                    p = copy.deepcopy(project)
                    overrides = slave.image.project_overrides.get(name, {})
                    p.update(overrides)

                    repo = p.get('repo', {})

                    args = {
                        'name': name,
                        'repo': repo.get('name', name),
                        'branch': p['repo'].get('branch', None),
                        'slaves': [slave.name],
                        'deps': p.get('deps', []),
                        'packages': p.get('packages', []),
                        'test': p.get('test', False),
                        'build': p.get('build', True)
                        }

                    if 'compile' in p: args['compile_command'] = p['compile']

                    f.write('add_build_project(**%s)\n' % args.__repr__())


        finally:
            if f is not None: f.close()


    def prepare_start(self):
        # Generate buildmaster config
        self.gen_config()

        # Expose ports
        host = self.conf['host']
        cmd = ['-p', '%s:%d:80' % (host, self.conf['http-port'])]
        if 'buildbot-port' in self.conf:
            cmd += ['-p', '%s:%d:9989' % (host, self.conf['buildbot-port'])]
        if 'github-port' in self.conf:
            cmd += ['-p', '%s:%d:8080' % (host, self.conf['github-port'])]

        return cmd, {}
