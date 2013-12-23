#!/usr/bin/env python
import unittest
import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(".."))
from xonrequest import Xor

simple_rule = {'route': '/t1/<val1>',
        'output': True,
        'type': 'run_script',
        'script': 'slow.sh'}

class RunscriptSlowTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_slow_printing(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        test_string = '1 2 3 4 5 6'
        rv = client.get('/t1/%s' % test_string)
        self.assertEqual(test_string, rv.data.strip())

if __name__ == '__main__':
    unittest.main()
