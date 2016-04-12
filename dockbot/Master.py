import os
import dockbot


local_cfg_hdr = '''\
# -*- python -*-
# Autogenerated file

c['projectName'] = '%(project)s'
c['projectURL'] = '%(url)s'
c['debugPassword'] = '%(passwd)s'
'''


class Master(dockbot.Container):
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

            # Gather slave projects
            slave_projects = {}
            for slave in self.image.root.slaves:
                for project in slave.deps:
                    if project not in slave_projects:
                        slave_projects[project] = set()

                    for container in slave.containers:
                        slave_projects[project].add(container.name)

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
            # for p in project_order: print p['name']

            # Slaves
            f.write('\n# Slaves\n')
            for slave in self.image.root.slaves:
                args = {
                    'name': slave.name,
                    'password': self.conf['passwd'],
                    'types': [],
                    'root': '/host',
                    'configs': slave.modes
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
                repo = project.get('repo', {})

                args = {
                    'name': project['name'],
                    'repo': repo.get('name', project['name']),
                    'branch': project['repo'].get('branch', None),
                    'slaves': list(slave_projects.get(project['name'], [])),
                    'deps': project.get('deps', []),
                    'packages': project.get('packages', []),
                    'test': project.get('test', False),
                    'build': project.get('build', True)
                    }

                if 'compile' in project:
                    args['compile_command'] = project['compile']

                f.write('add_build_project(**%s)\n' % args.__repr__())


        finally:
            if f is not None: f.close()


    def prepare_start(self):
        # Prepare run directory
        publish = os.path.dirname(__file__) + '/publish.py'
        dockbot.publish_file(publish, self.run_dir)

        # Generate buildmaster config
        self.gen_config()

        # Expose ports
        cmd = ['-p', '%s:%s:80' % (
                self.conf['ip'], self.conf.get('http-port', 8080)),
               '-p', '%s:%s:9989' % (
                self.conf['ip'], self.conf.get('buildbot-port', 9989))]

        return cmd
