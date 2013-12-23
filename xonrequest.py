#!/usr/bin/env python

import subprocess
import json

import flask


def main(argv):
    config_rules = json.load(open(argv[1]))
    x = Xor()
    x.add_rules(config_rules)
    x.app.run(host='0.0.0.0', debug=True)
    #x.app.run(host='0.0.0.0', debug=False)

def make_f(r):
    def f(**x):
        args = x.values()
        cmd = ['bash', r['script']] + args
        if 'user' in r:
            running_user = subprocess.check_output(['whoami']).strip()
            if r['user'] != running_user and running_user == 'root':
                cmd = ['sudo', '-u', r['user']] + cmd
            elif r['user'] != running_user:
                raise Exception('Permission denied')

        if r.get('output'):
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, bufsize=2)
            if p.returncode:
                print p.returncode
            return flask.Response(flask.stream_with_context(iter(lambda: p.stdout.read(1),'')))
        else:
            return str(subprocess.call(cmd))
    return f

class Xor(object):
    def __init__(self):
        self.app = flask.Flask(__name__)

    def add_rules(self, cfg):
        for rule in cfg:
            if 'route' not in rule:
                continue
            if rule.get('type') == 'run_script' and 'script' in rule:
                endpoint = 'f%s' % str(hash(rule['route']))
                self.app.add_url_rule(rule['route'], endpoint, make_f(rule),
                                      methods=rule.get('methods'),
                                      defaults=rule.get('defaults'))

if __name__ == '__main__':
    import sys
    main(sys.argv)
