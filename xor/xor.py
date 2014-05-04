#!/usr/bin/env python

import json
import os
import signal
import subprocess
import time
from urllib2 import quote, unquote, urlopen
from urllib import urlencode, unquote_plus
import urlparse
import tempfile

import requests
import flask
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import OrderedMultiDict


DEBUG = True


class XorRequestHandler(WSGIRequestHandler):
    # pylint: disable=R0904
    def connection_dropped(self, error, environ=None):
        if flask.g.proc:
            process = flask.g.proc
            print "Killing process: ", process
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()


def main(argv):
    config_rules = json.load(open(argv[1]))
    xor = Xor()
    xor.add_rules(config_rules)
    xor.app.run(host='0.0.0.0', debug=DEBUG, extra_files=[argv[1]],
                threaded=True, request_handler=XorRequestHandler)


def read_generator(file_d, size):
    while True:
        data = file_d.read(size)
        if not data:
            break
        print 'yielding data', data
        yield data


def escape_arg(arg):
    chars = [';', '>', '<', '|', '&']
    for char in chars:
        arg = arg.replace(char, '\\%s' % char)
    return arg


class Xor(object):
    def __init__(self):
        self.app = flask.Flask(__name__)

    def add_rules(self, cfg):
        for r in cfg:
            rule = r.copy()
            if 'route' not in rule:
                continue
            if 'arg_order' not in rule:
                arg_order = ['query', 'path', 'post']
            else:
                arg_order = rule.pop('arg_order')
            if 'script' in rule or 'command' in rule:
                route = rule.pop('route')
                endpoint = 'f%s' % str(hash(route))
                methods = rule.pop('methods', None)
                defaults = rule.pop('defaults', None)
                self.app.add_url_rule(route, endpoint,
                                      Xor.__create_view(route, arg_order=arg_order,
                                                        **rule),
                                      methods=methods, defaults=defaults)

    # Function factory, because of late binding.
    @staticmethod
    def __create_view(route, output=False, arg_order=None, user=None,
                      script=None, command=None, require_in_redir=False,
                      in_redir=False, out_redir=False, **options):
        if not arg_order:
            arg_order = []
        if require_in_redir:
            in_redir = True

        def view(**kwargs):
            query_args = Xor.__get_query_args(flask.request)
            post_args = Xor.__get_post_args(flask.request)
            if DEBUG:
                print flask.request.method, flask.request.url
                print 'Query args:\t', query_args
            stdin_file = None
            stdout_file = None
            if in_redir:
                stdin_file = (post_args.poplist('<') +
                              query_args.poplist('<') +
                              [None])[0]
                if require_in_redir and not stdin_file:
                    raise Exception
            if out_redir:
                stdout_file = (post_args.poplist('>') +
                               query_args.poplist('>') +
                               [None])[0]
            args = {}
            args['path'] = Xor.__get_path_args(kwargs, route)
            if DEBUG:
                print 'Path args:\t', args['path']

            args['query'] = map(Xor.__arg_to_string,
                                query_args.items(multi=True))
            args['post'] = map(Xor.__arg_to_string,
                               post_args.items(multi=True))
            arg_list = Xor.__order_args(arg_order, args)
            if script:
                this_cmd = [script] + arg_list
            else:
                arg_list = map(escape_arg, arg_list)
                this_cmd = [' '.join([command] + arg_list)]
            if DEBUG:
                print 'Command parsed:', this_cmd
            return Xor.__run_cmd(this_cmd, user=user, output=output,
                                 script=script, stdin_file=stdin_file,
                                 stdout_file=stdout_file)
        return view

    @staticmethod
    def __run_cmd(cmd, user=None, output=False, script=False, stdin_file=None,
                  stdout_file=None):
        def stream_url(url, outstream):
            r = requests.get(url, stream=True)
            for c in r.iter_content():
                print "wrote ", c
                outstream.write(c)
            outstream.close()
            print "done with writing"

        stdout = subprocess.PIPE
        stdin = None
        if stdout_file:
            output = False
            stdout = open(stdout_file, 'w')
        if stdin_file:
            if stdin_file.startswith('http'):
                stdin = subprocess.PIPE
            else:
                stdin = open(stdin_file)
        if user:
            running_user = subprocess.check_output(['whoami']).strip()
            if user != running_user:
                if running_user == 'root':
                    cmd = ['sudo', '-u', user] + cmd
                else:
                    raise Exception('Permission denied')
        try:
            process = subprocess.Popen(cmd, stdout=stdout, stdin=stdin,
                                       stderr=subprocess.STDOUT,
                                       bufsize=0, preexec_fn=os.setsid,
                                       close_fds=True, shell=(not script))
            if stdin_file and stdin_file.startswith('http'):
                def unquote_host_part(url):
                    url = unquote_plus(url)
                    li = list(urlparse.urlsplit(url))
                    li[2] = quote(li[2])  # quote path
                    qsl = urlparse.parse_qsl(li[3], True)
                    li[3] = urlencode(qsl)  # quote query
                    return urlparse.urlunsplit(li)
                stdin_url = unquote_host_part(stdin_file)
                if DEBUG:
                    print 'Opening url:', stdin_url
                stream_url(stdin_url, process.stdin)

            flask.g.proc = process
            if output:
                stream = read_generator(process.stdout, 1)
                return flask.Response(flask.stream_with_context(stream))
            else:
                process.communicate()
                exit_value = process.returncode
        except OSError as error:
            exit_value = error.errno
            if output:
                raise error
        return flask.make_response(str(exit_value))

    @staticmethod
    def __get_path_args(kwargs, route):
        res = []
        route_vars = route.split('/')
        for var in route_vars:
            if var.startswith('<') and var.endswith('>'):
                var = var[1:-1]
                index = var.find(':')
                res.append(var[index+1:])
        return [unicode(kwargs[x]) for x in res]

    @staticmethod
    def __get_query_args(req):
        d = OrderedMultiDict()
        if len(req.query_string) > 0:
            arg_list = req.query_string.split('&')
            arg_list = map(unquote, arg_list)
            for arg in arg_list:
                spl = arg.split('=', 1)
                spl.append(None)
                d.add(spl[0], spl[1])
        return d

    @staticmethod
    def __get_post_args(req):
        d = OrderedMultiDict()
        if req.method == 'POST':
            content = req.environ['wsgi.input']
            post_data = content.read(req.content_length)
            arg_list = post_data.split('&')
            arg_list = map(unquote, arg_list)
            for arg in arg_list:
                spl = arg.split('=', 1)
                spl.append(None)
                d.add(spl[0], spl[1])
        return d

    @staticmethod
    def __arg_to_string(arg):
        if not arg[1]:
            return arg[0]
        else:
            return u'%s=%s' % arg

    @staticmethod
    def __order_args(order, args):
        arg_list = []
        for arg_group in order:
            if arg_group in ['query', 'path', 'post']:
                arg_list.extend(args.get(arg_group,[]))
                del args[arg_group]
        return arg_list


if __name__ == '__main__':
    import sys
    main(sys.argv)
