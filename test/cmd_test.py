#!/usr/bin/env python
import unittest
import os
import sys
import subprocess
from urllib2 import quote
sys.path.insert(0, os.path.abspath(".."))
from xonrequest import Xor

simple_rule = {'route': '/t1/<val1>',
        'output': True,
        'command': 'echo'}
rule2 = {'route': '/t2/',
        'output': True,
        'command': 'cat'}

class CmdArgTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_echo(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        rv = client.get('/t1/cba')
        test_string = 'cba'
        self.assertEqual(test_string, rv.data.strip())

    def test_cat_file(self):
        self.x.add_rules([rule2])
        client = self.x.app.test_client()
        filename = '/etc/passwd'
        rv = client.get('/t2/?' + quote(filename))
        test_string = open(filename).read()
        self.assertEqual(test_string, rv.data)


if __name__ == '__main__':
    unittest.main()