#!/usr/bin/env python
import unittest
import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(".."))
from xonrequest import Xor

simple_rule = {'route': '/t1/<val2>/<val4>/<val1>/<val3>',
               'methods': ['GET', 'POST'],
               'output': True,
               'script': 'echo.sh'}

rule2 = {'route': '/t2/<path:val1>/<val2>/<val3>/<int:val4>',
         'output': True,
         'script': 'echo.sh'}

rule3 = {'route': '/t1',
         'methods': ['GET', 'POST'],
         'output': True,
         'script': 'echo.sh'}

class VarsTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_ordered_path_args(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        test_string = "/".join('1234')
        result_string = " ".join('1234')
        rv = client.get('/t1/%s' % test_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_special_chars_path_args(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        a = '"\\\''
        b = ';_;#--'
        c = '"abc;def;ghi"'
        d = '| %less'
        test_string = "%s/%s/%s/%s" % (a, b, c, d)
        result_string = "%s %s %s %s" % (a, b, c, d)
        rv = client.get('/t1/%s' % test_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_special_chars_path_args2(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        a = '> file'
        b = '>><<'
        c = '"abc;def;ghi"'
        d = '&& ls'
        test_string = "%s/%s/%s/%s" % (a, b, c, d)
        result_string = "%s %s %s %s" % (a, b, c, d)
        rv = client.get('/t1/%s' % test_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_converters(self):
        self.x.add_rules([rule2])
        client = self.x.app.test_client()
        a = 'dev/null'
        b = 'string'
        c = 'somethingelse'
        d = '553'
        test_string = "%s/%s/%s/%s" % (a, b, c, d)
        result_string = "%s %s %s %s" % (a, b, c, d)
        rv = client.get('/t2/%s' % test_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_ordered_query_args(self):
        self.x.add_rules([rule3])
        client = self.x.app.test_client()
        args = ['1=q', '"a=k', '--f=a', 'w', '/dev/null', 'f=../../sdd/']
        test_string = "&".join(args)
        result_string = " ".join(args)
        rv = client.get('/t1?%s' % test_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_ordered_post_args(self):
        self.x.add_rules([rule3])
        client = self.x.app.test_client()
        args = ['1=q', '"a=k', '--f=a', 'w', '/dev/null', 'f=../../sdd/']
        data_string = "&".join(args)
        result_string = " ".join(args)
        rv = client.post('/t1', data=data_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_mixed_args(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        path_args = ['abc', '123', '"\\"', '<>']
        query_args = ['~/file', '-d=,#']
        post_args = ['<str','/dev/true','--value none']
        path = '/'.join(path_args)
        query_string = '&'.join(query_args)
        data_string = '&'.join(post_args)
        result_string = ' '.join(path_args + query_args + post_args)
        rv = client.post('/t1/%s?%s' % (path, query_string), data=data_string)
        self.assertEqual(result_string, rv.data.strip())

if __name__ == '__main__':
    unittest.main()
