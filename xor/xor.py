#!/usr/bin/env python

import subprocess as subp
from urllib2 import unquote
import json
import os
import signal

from flask import Flask, request, Response, stream_with_context, g
from werkzeug.serving import WSGIRequestHandler


DEBUG = True


class XorRequestHandler(WSGIRequestHandler):
    def connection_dropped(self, error, environ=None):
        if g.proc:
            print "Killing process: ", g.proc
            os.killpg(g.proc.pid, signal.SIGKILL)
            g.proc.communicate()


def main(argv):
    config_rules = json.load(open(argv[1]))
    x = Xor()
    x.add_rules(config_rules)
    x.app.run(host='0.0.0.0', debug=DEBUG, extra_files=[argv[1]],
              request_handler=XorRequestHandler)


def read_generator(fd, b):
    return iter(lambda: fd.read(b), '')


def run_cmd(cmd, user=None, output=False, script=False):
    if user:
        running_user = subp.check_output(['whoami']).strip()
        if user != running_user:
            if running_user == 'root':
                cmd = ['sudo', '-u', user] + cmd
            else:
                raise Exception('Permission denied')
    if output:
        p = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.STDOUT,
                       bufsize=2, preexec_fn=os.setsid, shell=(not script))
        g.proc = p
        return Response(stream_with_context(read_generator(p.stdout, 1)))
    else:
        try:
            p = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.STDOUT,
                           preexec_fn=os.setsid, shell=(not script))
            (a, b) = p.communicate()
            exit_value = p.returncode
        except OSError as e:
            print e
            exit_value = e.errno
        return str(exit_value)


def get_path_args(kwargs, route):
    def get_vars(route):
        res = []
        vs = route.split('/')
        for v in vs:
            if v.startswith('<') and v.endswith('>'):
                v = v[1:-1]
                ind = v.find(':')
                res.append(v[ind+1:])
        return res
    return [unicode(kwargs[x]) for x in get_vars(route)]


def get_query_args(request):
    if len(request.query_string) > 0:
        query_string = unquote(request.query_string)
        return query_string.split('&')
    else:
        return []


def get_post_args(request):
    if request.method == 'POST':
        content = request.environ['wsgi.input']
        post_data = unquote(content.read(request.content_length))
        return post_data.split('&')
    else:
        return []


def order_args(order, args):
    arg_list = []
    for o in order + ['query', 'path', 'post']:
        if o in args:
            arg_list.extend(args[o])
            del args[o]
    return arg_list


# Function factory, because of late binding.
def create_view(route=None, output=False, order=None, user=None, script=None,
                command=None, **options):
    if not route:
        raise Exception
    if not order:
        order = ['query', 'path', 'post']

    def view(**kwargs):
        args = {}
        args['path'] = get_path_args(kwargs, route)
        args['query'] = get_query_args(request)
        args['post'] = get_post_args(request)
        arg_list = order_args(order, args)
        if script:
            this_cmd = [script] + arg_list
        else:
            arg_list = safe_args(arg_list)
            this_cmd = [' '.join([command] + arg_list)]
        if DEBUG:
            print this_cmd
        return run_cmd(this_cmd, user=user, output=output, script=script)
    return view

def safe_args(li):
    chars = ';>|&'
    res = []
    for arg in li:
        for c in chars:
            arg = arg.replace(c, '\\%s' % c)
        res.append(arg)
    return res


class Xor(object):
    def __init__(self):
        self.app = Flask(__name__)

    def add_rules(self, cfg):
        for rule in cfg:
            if 'route' not in rule:
                continue
            if 'script' in rule or 'command' in rule:
                endpoint = 'f%s' % str(hash(rule['route']))
                self.app.add_url_rule(rule['route'], endpoint,
                                      create_view(**rule),
                                      methods=rule.get('methods'),
                                      defaults=rule.get('defaults'))

if __name__ == '__main__':
    import sys
    main(sys.argv)
