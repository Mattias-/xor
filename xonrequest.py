#!/usr/bin/env python

import subprocess
import json

from flask import Flask


def main(argv):
    config_rules = json.load(open(argv[1]))
    x = Xor()
    x.add_rules(config_rules)
    #x.app.run(host='0.0.0.0', debug=True)
    x.app.run(host='0.0.0.0', debug=False)


class Xor(object):
    def __init__(self):
        self.app = Flask(__name__)

    def add_rules(self, cfg):
        for rule in cfg:
            if 'route' not in rule:
                continue
            if rule.get('type') == 'run_script' and 'script' in rule:
                def make_f(r):
                    def f(**x):
                        cmd = ['bash', r['script']]
                        cmd.extend(x.values())
                        if r.get('output'):
                            return subprocess.check_output(cmd)
                        else:
                            return str(subprocess.call(cmd))
                    return f
                endpoint = 'f%s' % str(hash(rule['route']))
                self.app.add_url_rule(rule['route'], endpoint, make_f(rule),
                                      methods=rule.get('methods'),
                                      defaults=rule.get('defaults'))

if __name__ == '__main__':
    import sys
    main(sys.argv)
