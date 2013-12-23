#!/usr/bin/env python
import subprocess

from flask import Flask, request


class Xor(object):
    def __init__(self):
        self.app = Flask(__name__)

    def add_rules(self, cfg):
        for d in cfg:
            if not 'route' in d:
                continue
            if d.get('type') == 'run_script' and 'script' in d:
                def make_f(r):
                    def f(**x):
                        cmd = ['bash', r['script']]
                        #cmd.extend(["%s=%s" % arg for arg in request.args.items()])
                        cmd.extend(x.values())
                        #[str(request.form.items())]
                        if r.get('output') == True:
                            return subprocess.check_output(cmd)
                        else:
                            return str(subprocess.call(cmd))
                    return f
                endpoint = 'f%s' % str(hash(d['route']))
                self.app.add_url_rule(d['route'], endpoint, make_f(d),
                                      methods=d.get('methods'),
                                      defaults=d.get('defaults'))

if __name__ == '__main__':
    import json
    import sys
    cfg = json.load(open(sys.argv[1]))
    x = Xor()
    x.add_rules(cfg)
    #x.app.run(host='0.0.0.0', debug=True)
    x.app.run(host='0.0.0.0', debug=False)
