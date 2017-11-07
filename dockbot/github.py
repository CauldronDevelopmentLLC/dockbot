#!/usr/bin/env python

import re
import json
import os
import time
import sys
from optparse import OptionParser
import requests
from requests.auth import HTTPBasicAuth


api_url = 'https://api.github.com'
releases_path = '/repos/%(org)s/%(repo)s/releases'
releases_url = api_url + releases_path
default_org = 'FoldingAtHome'
default_body = 'See [CHANGELOG.md]' + \
    '(https://github.com/%(org)s/%(repo)s/blob/master/CHANGELOG.md).'
default_title = 'v%(version)s %(mode)s'

usage = '''\
Usage: %prog <command> [options...] [assets...]

Commands:
  list       List releases or release assets
  get        Get an existing release or release asset
  create     Create a new draft release
  publish    Publish a draft release
  delete     Delete an existing release or release asset
  upload     Upload a release asset
  download   Download a release asset

Assets:
  May be asset ids, file names or glob patterns.
'''


class GitHubError(Exception):
    pass


def pretty_print_json(data):
    print json.dumps(data, indent = 2, separators = (',', ': '))


def human_size(size, suffix = 'B'):
    if size < 1024:
        if isinstance(size, float): return '%.1f%s' % (size, suffix)
        else: return '%d%s' % (size, suffix)

    size /= 1024.0

    if suffix: suffix = 'i' + suffix

    for unit in 'KMGTPEZ':
        if abs(size) < 1024.0:
            return "%.1f%s%s" % (size, unit, suffix)
        size /= 1024.0

    return "%.1fY%s" % (size, suffix)


def human_time(t):
    for label, x in [('s', 60), ('m', 60), ('h', 24), ('d', 365), ('y', None)]:
        if x is None or t < x: return '%.1f%s' % (t, label)
        t /= float(x)


def github_auth(opts):
    if (not opts['token']) and opts['user'] and opts['passwd']:
        if opts['debug']: print 'Using user/pass authentication'
        return HTTPBasicAuth(opts['user'], opts['passwd'])


def github_request(opts, method, url, **kwargs):
    if url.find('%(id)d') != -1 and opts.get('id', None) is None:
        r = github_get(opts, releases_url + '/tags/%(tag)s')
        opts['id'] = int(r['id'])

    url = url % opts

    if opts['debug']: print '%s %s' % (method, url)

    hdrs = None
    if opts['token']:
        if not 'headers' in kwargs: kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = 'token %(token)s' % opts

    r = requests.request(method, url, auth = github_auth(opts), **kwargs)

    if 300 <= r.status_code:
        if r.headers['Content-Type'].startswith('application/json'):
            if opts['debug']: pretty_print_json(r.json())
            raise GitHubError, 'Error: ' + r.json()['message']

        r.raise_for_status()

    if r.status_code != requests.codes.no_content:
        return r.json()


def github_get(opts, path, **kwargs):
    return github_request(opts, 'GET', path)


def github_post(opts, path, **kwargs):
    return github_request(opts, 'POST', path, **kwargs)


def github_patch(opts, path, **kwargs):
    return github_request(opts, 'PATCH', path, **kwargs)


def github_delete(opts, path, **kwargs):
    return github_request(opts, 'DELETE', path, **kwargs)


def print_release(release):
    print '%(tag_name)s #%(id)d %(created_at)s %(name)s' % release


def print_asset(asset):
    asset['hsize'] = human_size(asset['size'], '')
    print '%(name)s #%(id)d %(created_at)s %(hsize)s' % asset


def get_release_mode(release):
    parts = release['name'].split()
    if len(parts) == 2: return parts[1]


def get_latest_release(opts):
    releases = github_get(opts, releases_url)
    for release in releases:
        if not opts['mode'] or opts['mode'] == get_release_mode(release):
            return release


def list_releases(opts):
    map(print_release, github_get(opts, releases_url))


def get_release(opts):
    url = releases_url

    if opts['id']: url += '/%(id)d'
    else: url += '/tags/%(tag)s'

    return github_get(opts, url)


def create_release(opts):
    data = {
        'tag_name': opts['tag'],
        'name': opts['title'] % opts,
        'body': opts['body'] % opts,
        'draft': True,
        }
    r = github_post(opts, releases_url, json = data)
    opts['id'] = int(r['id'])
    opts['upload_url'] = r['upload_url']

    print 'Created draft release %(id)s' % opts


def publish_release(opts):
    github_patch(opts, releases_url + '/%(id)d', json = {'draft': False})

    print 'Published release %(tag)s' % opts


def delete_release(opts):
    github_delete(opts, releases_url + '/%(id)d')

    print 'Deleted release %(id)d' % opts


def get_release_assets(opts):
    return github_get(opts, releases_url + '/%(id)d/assets')


def list_release_assets(opts):
    map(print_asset, get_release_assets(opts))


def match_release_assets(opts, name):
    import fnmatch

    assets = get_release_assets(opts)
    matches = []

    for asset in assets:
        if fnmatch.fnmatch(asset['name'], name) or str(asset['id']) == name:
            if opts['debug']: print json.dumps(asset)
            matches.append(asset)

    if len(matches): return matches
    raise GitHubError, 'Asset "%s" not found' % name


class Progress(object):
    def __init__(self, size, period = 1):
        self.size = size
        self.period = period

        self.position = 0
        self.last = 0
        self.last_bytes = 0


    def update(self, count):
        self.position += count

        if not self.last: self.last = time.time()
        if not self.position or time.time() - self.last < self.period:
            return

        size = human_size(self.position)
        if self.size: percent = float(self.position) / self.size * 100
        else: percent = 0
        now = time.time()

        deltaSize = self.position - self.last_bytes
        deltaTime = now - self.last
        if deltaSize and deltaTime:
            rate = deltaSize / deltaTime
            eta = human_time((self.size - self.position) / rate)
            rate = human_size(deltaSize / deltaTime)

        else:
            eta = 'unknown'
            rate = 0

        print '\r%s %0.1f%% %s/sec ETA %s%s' % (
            size, percent, rate, eta, ' ' * 16),
        sys.stdout.flush()

        self.last = now
        self.last_bytes = self.position


class ProgressFile(object):
    def __init__(self, path):
        import mmap

        self.path = path

        if not os.path.exists(path):
            raise GitHubError, 'Cannot access "%(path)s"' % path

        self.size = os.path.getsize(path)

        self.file = open(path, 'rb')
        self.mmap = mmap.mmap(self.file.fileno(), 0, access = mmap.ACCESS_READ)
        self.position = 0
        self.progress = Progress(self.size)


    def read(self, size = -1):
        space = self.size - self.position
        if size == -1: size = space
        if space < size: size = space
        data = self.mmap[self.position:self.position + size]

        self.progress.update(size)
        self.position += size

        return data


    def __len__(self): return self.size


    def close(self):
        self.mmap.close()
        self.file.close()
        self.progress.update(0)


def upload_release_asset(opts, path):
    name = os.path.basename(path)
    opts['asset'] = name

    if 'upload_url' not in opts:
        r = get_release(opts)
        opts['upload_url'] = r['upload_url']

    url = opts['upload_url']
    url = re.sub(r'\{[^}]*\}', '', url)
    url += '?name=%(asset)s'

    if not os.path.exists(path):
        raise GitHubError, 'Cannot access "%s"' % path

    f = None
    try:
        f = ProgressFile(path)

        print 'Uploading %s %s' % (opts['asset'], human_size(f.size))

        import magic
        m = magic.open(magic.MAGIC_MIME)
        m.load()

        headers = {'Content-Type': m.file(path)}

        github_post(opts, url, data = f, headers = headers)

    finally:
        if f is not None: f.close()

    print


def delete_release_asset(opts, path):
    name = os.path.basename(path)

    for asset in match_release_assets(opts, name):
        github_delete(opts, releases_url + '/assets/%(id)d' % asset)
        print '%(name)s deleted' % asset


def download_release_asset(opts, pattern):
    for asset in match_release_assets(opts, pattern):
        if not opts['force'] and os.path.exists(asset['name']):
            raise GitHubError, 'Asset "%(name)s" already exists' % asset

        print 'Downloading %s %s' % (asset['name'], human_size(asset['size']))

        hdrs = {'Accept': 'application/octet-stream'}
        if opts['token']: hdrs['Authorization'] = 'token %(token)s' % opts

        progress = Progress(asset['size'])
        r = requests.get(asset['url'], auth = github_auth(opts), headers = hdrs,
                         stream = True)

        with open(asset['name'], 'wb') as f:
            for chunk in r.iter_content(chunk_size = 10240):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))

        print


def run():
    parser = OptionParser(usage = usage)
    parser.add_option('-u', '--user', help = 'GitHub user name', dest = 'user')
    parser.add_option('-p', '--pass', help = 'GitHub password or access token',
                      dest = 'passwd')
    parser.add_option('-o', '--org', help = 'GitHub organization', dest = 'org')
    parser.add_option('-r', '--repo', help = 'GitHub repository',
                      dest = 'repo')
    parser.add_option('-i', '--id', help = 'GitHub release id',
                      dest = 'id', type = 'int')
    parser.add_option('-b', '--body', help = 'Text for GitHub release body',
                      dest = 'body', default = default_body)
    parser.add_option('-t', '--title', help = 'Text for GitHub release title',
                      dest = 'title', default = default_title)
    parser.add_option('-v', '--version', help = 'GitHub release version',
                      dest = 'version')
    parser.add_option('-m', '--mode', help = 'GitHub release mode',
                      dest = 'mode')
    parser.add_option('-d', '--debug', help = 'Print debug info',
                      dest = 'debug', action = 'store_true')
    parser.add_option('-c', '--create', help = 'When uploading, create release '
                      'if it does not already exist', dest = 'create',
                      action = 'store_true')
    parser.add_option('-l', '--latest', help = 'Operate on latest release',
                      dest = 'latest', action = 'store_true')
    parser.add_option('-f', '--force', help = 'Overwrite existing files',
                      dest = 'force', action = 'store_true')
    parser.add_option('-k', '--token', help = 'GitHub auth token',
                      dest = 'token')
    options, args = parser.parse_args()

    # Process args
    if len(args) < 1: parser.error('Missing command')
    cmd = args[0]
    assets = args[1:]

    opts = vars(options)
    if not (options.user or options.token):
        parser.error('User or token required')
    if not options.repo: parser.error('Repo required')
    if not options.org: parser.error('Org required')

    import getpass
    while not (options.token or options.passwd):
        options.passwd = \
            getpass.getpass("%s's GitHub Password: " % options.user)

    def has_tag():
        return options.version and options.mode

    if options.latest:
        if options.id: parser.error('Do not specify "id" with "latest"')
        if options.version:
            parser.error('Do not specify "version" with "latest"')

        latest = get_latest_release(opts)
        if latest is None: parser.error('No matching releases found')
        opts['id'] = latest['id']
        options.id = latest['id']

    if cmd != 'list':
        if not (options.id or has_tag()):
            parser.error('Release "id", "version" and "mode" or "latest" '
                         'required')

    if has_tag():
        if not re.match(r'^\d+\.\d+\.\d+$', options.version):
            parser.error('Version must be of the format: <major>.<minor>.<rev>')

        if options.mode not in ('release', 'debug'):
            parser.error('Mode must be one of "release" or "debug"')

        opts['tag'] = '%(version)s-%(mode)s' % opts

    # Execute command
    try:
        if cmd == 'list':
            if has_tag() or options.id: list_release_assets(opts)
            else: list_releases(opts)

        elif cmd == 'get':
            if len(assets):
                for asset in assets:
                    for match in match_release_assets(opts, asset):
                        print_asset(match)

            else: print_release(get_release(opts))

        elif cmd == 'create': create_release(opts)
        elif cmd == 'publish': publish_release(opts)

        elif cmd == 'delete':
            if len(assets):
                for asset in assets:
                    try:
                        delete_release_asset(opts, asset)
                    except GitHubError as e:
                        print e.message

            else: delete_release(opts)

        elif cmd == 'upload':
            if not len(assets): parser.error('No assets to upload')

            if options.create:
                try:
                    get_release(opts)
                except GitHubError:
                    create_release(opts)

            for asset in assets:
                try:
                    upload_release_asset(opts, asset)
                except GitHubError as e:
                    print e.message

        elif cmd == 'download':
            if not len(assets): assets = ['*']
            for asset in assets: download_release_asset(opts, asset)

        else: parser.error('Unsupported command "%s"' % cmd)

    except GitHubError as e:
        print e.message


if __name__ == "__main__": run()
