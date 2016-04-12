import collections


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r

        else: d[k] = u[k]

    return d


class Config(object):
    def __init__(self, config):
        self.config = config

        self.projects = []

        if 'projects' in config:
            if '_default_' in config['projects']:
                default = config['projects']['_default_']
            else: default = {}

            for name, project in config['projects'].items():
                if name == '_default_': continue

                data = {'name': name}
                update(data, default)
                update(data, project)

                self.projects.append(data)


    def get(self, key, default = None):
        return self.config.get(key, default)


    def __contains__(self, key):
        return self.config.__contains__(key)


    def __getitem__(self, key):
        return self.config.__getitem__(key)


    def __setitem__(self, key, value):
        self.config.__setitem__(key, value)


    def enum_by_key(self, key, mode = None):
        if key in self.config: yield self.config[key]

        if 'modes' in self.config and mode in self.config['modes'] and \
                key in self.config['modes'][mode]:
            yield self.config['modes'][mode][key]


    def enum_by_sub_key(self, name, key, mode = None):
        if name in self.config:
            for x in Config(self.config[name]).enum_by_key(key, mode):
                yield x


    def enum(self, key, name, slave, mode = None):
        for x in self.enum_by_key(key, mode): yield x

        if slave:
            for x in self.enum_by_sub_key('slaves', key, mode): yield x
        else:
            for x in self.enum_by_sub_key('master', key): yield x

        for x in self.enum_by_sub_key(name, key, mode): yield x


    def get_dict(self, key, name, slave, mode = None):
        d = {}
        for x in self.enum(key, name, slave, mode): d.update(x)
        return d


    def get_list(self, key, name, slave, mode = None):
        l = []
        for x in self.enum(key, name, slave, mode): l += x
        return l


    def get_project_deps(self, project):
        s = set()
        s.add(project)

        if project in self.config['projects']:
            for dep in self.config['projects'][project].get('deps', []):
                s.update(self.get_project_deps(dep))

        return s
