#!/usr/bin/env python
#
# WSGI app which forwards GitHub change notifications to Buildbot

import os
import sys
import json

from twisted.cred import credentials
from twisted.internet import reactor
from twisted.spread import pb

server = 'localhost'
port = 9989


def process_change(response, payload, server, port, user, repo, repo_url):
    branch = payload['ref'].split('/')[-1]

    if payload['deleted'] is True:
        response('200 OK', [])
        return ['Branch "%s" deleted, ignoring', branch]

    if not 'head_commit' in payload:
        response('200 OK', [])
        return ['No changes found']

    # Get all changed files
    files = []
    for c in payload['commits']:
        files += c['added'] + c['removed'] + c['modified']

    # Process head commit as change
    c = payload['head_commit']
    changes = [{
        'revision': c['id'],
        'revlink': c['url'],
        'who': c['author']['name'] + ' <' + c['author']['email'] + '> ',
        'comments': c['message'],
        'repo': repo_url,
        'files': files,
        'branch': branch,
        'category': repo,
    }]

    def connect_failed(error):
        print 'Connect failed: ' + error.getErrorMessage()

    def connected(remote, changes):
        return add_change(None, remote, changes.__iter__())

    factory = pb.PBClientFactory()
    deferred = factory.login(credentials.UsernamePassword('change', 'changepw'))
    reactor.connectTCP(server, port, factory)
    deferred.addErrback(connect_failed)
    deferred.addCallback(connected, changes)

    response('200 OK', [])
    return ['ok']


def add_change(dummy, remote, changei, src = 'git'):
    """Sends changes from the commit to the buildmaster."""
    try:
        change = changei.next()
    except StopIteration:
        remote.broker.transport.loseConnection()
        return None

    def add_change_failed(error):
        print 'Add change failed: ' + error.getErrorMessage()
        remote.broker.transport.loseConnection()

    change['src'] = src
    deferred = remote.callRemote('addChange', change)
    deferred.addCallback(add_change, remote, changei, src)
    deferred.addErrback(add_change_failed)

    return deferred


def app(env, response):
    if env['REQUEST_METHOD'] == 'GET':
        response('200 OK', [])
        return ['hello']

    elif env['REQUEST_METHOD'] != 'POST':
        response('403 Forbidden', [])
        return ['Request method not allowed']

    size = int(env.get('CONTENT_LENGTH', 0))
    body = env['wsgi.input'].read(size)
    payload = json.loads(body)

    user = payload['pusher']['name']
    repo = payload['repository']['name']
    repo_url = payload['repository']['url']

    return process_change(response, payload, server, port, user, repo, repo_url)
