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
Usage: %prog <command> [options]

Commands:
  list     List releases or release assets
  get      Get an existing release or release asset
  create   Create a new draft release
  publish  Publish a draft release
  delete   Delete an existing release or release asset
  upload   Upload a release asset
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


def github_request(opts, method, url, **kwargs):
    if url.find('%(id)d') != -1 and 'id' not in opts:
        r = github_get(opts, releases_url + '/tags/%(tag)s')
        opts['id'] = r['id']

    auth = HTTPBasicAuth(options.user, options.passwd)
    url = url % opts

    if opts['debug']: print '%s %s' % (method, url)

    r = requests.request(method, url, auth = auth, **kwargs)

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


def list_releases(opts):
    map(print_release, github_get(opts, releases_url))


def get_release(opts):
    return github_get(opts, releases_url + '/tags/%(tag)s')


def create_release(opts):
    data = {
        'tag_name': opts['tag'],
        'name': opts['title'] % opts,
        'body': opts['body'] % opts,
        'draft': True,
        }
    r = github_post(opts, releases_url, json = data)
    opts['id'] = r['id']
    opts['upload_url'] = r['upload_url']

    print 'Created draft release %(id)s' % opts


def publish_release(opts):
    github_patch(opts, releases_url + '/%(id)d', json = {'draft': False})

    print 'Published release %(tag)s' % opts


def delete_release(opts):
    github_delete(opts, releases_url + '/%(id)d')

    print 'Deleted release %(tag)s' % opts


def get_release_assets(opts):
    return github_get(opts, releases_url + '/%(id)d/assets')


def list_release_assets(opts):
    map(print_asset, get_release_assets(opts))


def get_release_asset(opts, name):
    assets = get_release_assets(opts)

    for asset in assets:
        if asset['name'] == name: return asset

    raise GitHubError, 'Asset "%s" not found' % name


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
        self.last = 0
        self.last_bytes = 0


    def progress(self):
        size = human_size(self.position)
        percent = float(self.position) / self.size * 100
        now = time.time()
        deltaSize = self.position - self.last_bytes
        deltaTime = now - self.last
        rate = deltaSize / deltaTime
        eta = human_time((self.size - self.position) / rate)
        rate = human_size(deltaSize / deltaTime)

        print '\r%s %0.1f%% %s/sec ETA %s%s' % (
            size, percent, rate, eta, ' ' * 16),
        sys.stdout.flush()

        self.last = now
        self.last_bytes = self.position


    def read(self, size = -1):
        space = self.size - self.position
        if size == -1: size = space
        if space < size: size = space
        data = self.mmap[self.position:self.position + size]

        if not self.last: last = time.time()
        if self.position and 1 < time.time() - self.last: self.progress()

        self.position += size

        return data


    def __len__(self):
        return self.size


    def close(self):
        self.mmap.close()
        self.file.close()
        self.progress()


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
    asset = get_release_asset(opts, name)
    github_delete(opts, releases_url + '/assets/%(id)d' % asset)
    print '%s deleted' % name


def run():
    parser = OptionParser(usage = usage)
    parser.add_option('-u', '--user', help = 'GitHub user name', dest = 'user')
    parser.add_option('-p', '--pass', help = 'GitHub password or access token',
                      dest = 'passwd')
    parser.add_option('-o', '--org', help = 'GitHub organization',
                      dest = 'org', default = default_org)
    parser.add_option('-r', '--repo', help = 'GitHub repository',
                      dest = 'repo')
    parser.add_option('-i', '--id', help = 'GitHub repository id',
                      dest = 'id')
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
    options, args = parser.parse_args()

    # Process args
    if len(args) < 1: parser.error('Missing command')
    cmd = args[0]
    assets = args[1:]

    opts = vars(options)
    if not options.user: parser.error('User required')
    if not options.passwd: parser.error('Password or access token required')
    if not options.repo: parser.error('Repo required')

    def has_tag():
        return options.version and options.mode

    if cmd != 'list':
        if not options.id or (options.version and options.mode):
            parser.error('Release id or version and mode required')

    if has_tag():
        if not re.match(r'^\d+\.\d+\.\d+$', options.version):
            parser.error('Version must be of the format: <major>.<minor>.<rev>')

        if options.mode not in ('release', 'debug'):
            parser.error('Mode must be one of "release" or "debug"')

        opts['tag'] = '%(version)s-%(mode)s' % opts

    # Execute command
    try:
        if cmd == 'list':
            if has_tag(): list_release_assets(opts)
            else: list_releases(opts)

        elif cmd == 'get':
            if len(assets):
                for asset in assets:
                    print_asset(get_release_asset(opts, asset))

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

        else: raise parser.error('Unsupported command "%s"' % cmd)

    except GitHubError as e:
        print e.message


if __name__ == "__main__": run()
