import collections


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r

        else: d[k] = u[k]

    return d


class Config(object):
    def __init__(self, conf):
        self.conf = conf

        self.projects = []

        if 'projects' in conf:
            if '_default_' in conf['projects']:
                default = conf['projects']['_default_']
            else: default = {}

            for name, project in conf['projects'].items():
                if name == '_default_': continue

                data = {'name': name}
                update(data, default)
                update(data, project)

                self.projects.append(data)


    def get(self, key, default = None):
        return self.conf.get(key, default)


    def __contains__(self, key):
        return self.conf.__contains__(key)


    def __getitem__(self, key):
        return self.conf.__getitem__(key)


    def __setitem__(self, key, value):
        self.conf.__setitem__(key, value)


    def enum_by_key(self, key, mode = None):
        if key in self.conf: yield self.conf[key]

        if 'modes' in self.conf and mode in self.conf['modes'] and \
                key in self.conf['modes'][mode]:
            yield self.conf['modes'][mode][key]


    def enum_by_sub_key(self, name, key, mode = None):
        if name in self.conf:
            for x in Config(self.conf[name]).enum_by_key(key, mode):
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

        if project in self.conf['projects']:
            for dep in self.conf['projects'][project].get('deps', []):
                s.update(self.get_project_deps(dep))

        return s
