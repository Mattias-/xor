

import json
import subprocess
import sys

from flask import Flask, request

app = Flask(__name__)

def setup(cfg):
    for d in cfg:
        if not 'route' in d:
            continue
        if d.get('type') == 'run_script' and 'script' in d:
            def f(**x):
                cmd = ['bash', d['script']]
                #cmd.extend(["%s=%s" % arg for arg in request.args.items()])
                cmd.extend(x.values())
                #[str(request.form.items())]
                if d.get('output', False):
                    return subprocess.check_output(cmd)
                else:
                    return str(subprocess.check_call(cmd))
            endpoint = 'f%s' % str(hash(d['route']))
            app.add_url_rule(d['route'], endpoint, f, methods=d.get('methods'),
                             defaults=d.get('defaults'))

if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    setup(cfg)
    app.run(host='0.0.0.0', debug=True)
