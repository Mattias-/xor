#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import unittest
from urllib2 import quote

from xor import Xor

script_path='tests/files/'
simple_rule = {'route': '/t1/<val2>/<val4>/<val1>/<val3>',
               'methods': ['GET', 'POST'],
               'output': True,
               'script': script_path+'echo.sh'}

rule2 = {'route': '/t2/<path:val1>/<val2>/<val3>/<int:val4>',
         'output': True,
         'script': script_path+'echo.sh'}

rule3 = {'route': '/t1',
         'methods': ['GET', 'POST'],
         'output': True,
         'script': script_path+'echo.sh'}

rule4 = {'route': '/nested',
         'methods': ['GET', 'POST'],
         'output': True,
         'script': script_path+'echoarg.sh'}

class VarsTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_nested_urls(self):
        self.x.add_rules([rule4])
        client = self.x.app.test_client()
        url1 = 'http://a.se/bb?c=d&e=f'
        url2 = 'http://b.se/gg?h&i&j=%s' % quote(url1, '')
        test_string = 'url1=%s&url2=%s' % (quote(url1, ''), quote(url2, ''))
        rv = client.get('/nested?url1&%s' % test_string)
        self.assertEqual(url1, rv.data.strip())
        rv2 = client.get('/nested?url2&%s' % test_string)
        self.assertEqual(url2, rv2.data.strip())


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
        c = '"abc;def;åäö"'
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

    def test_urlencoded_args(self):
        def quote_keyval(s):
            (before, sep, after) = s.partition('=')
            return quote(before) + sep + quote(after)
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        path_args = ['abc', '123', '"\\"', '<>']
        path_args_quoted = map(quote, path_args)
        query_args = ['~/file', '-d=a%26x=y']
        query_args_quoted = map(quote, query_args)
        post_args = ['<str','/dev/true','--val%26e=no%26ne']
        post_args_quoted = map(quote, post_args)
        path = '/'.join(path_args_quoted)
        query_string = '&'.join(query_args_quoted)
        data_string = '&'.join(post_args_quoted)
        result_string = ' '.join(query_args + path_args + post_args)
        rv = client.post('/t1/%s?%s' % (path, query_string), data=data_string)
        self.assertEqual(result_string, rv.data.strip())
        rv2 = client.post('/t1/%s?%s' % ('/'.join(path_args),
                                         '&'.join(query_args)),
                                        data='&'.join(post_args))
        self.assertNotEqual(result_string, rv2.data.strip())

    def test_converters(self):
        self.x.add_rules([rule2])
        client = self.x.app.test_client()
        path_args = ['~/files', 'asdas', 'whatever', '553']
        # Needs werkzeug patch
        #path_args[2] = '/dev/null'
        result_string = ' '.join(path_args)
        path_args[2] = quote(path_args[2], '')
        test_string = '/'.join(path_args)
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

    def test_bash_escape_query_arg(self):
        self.x.add_rules([rule3])
        client = self.x.app.test_client()
        test_string = "abc;echo def"
        rv = client.get('/t1?%s' % test_string)
        self.assertEqual(test_string, rv.data.strip())

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
        result_string = ' '.join(query_args + path_args + post_args)
        rv = client.post('/t1/%s?%s' % (path, query_string), data=data_string)
        self.assertEqual(result_string, rv.data.strip())

    def test_given_order(self):
        rule = simple_rule.copy()
        order = ['post', 'query', 'path']
        rule.update({'order': order})
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        path_args = ['abc', '123', 'def', '456']
        query_args = ['a=789', 'ghi']
        post_args = ['876','c=jkl','b=543']
        path = '/'.join(path_args)
        query_string = '&'.join(query_args)
        data_string = '&'.join(post_args)
        result_string = ' '.join(post_args + query_args + path_args)
        rv = client.post('/t1/%s?%s' % (path, query_string), data=data_string)
        self.assertEqual(result_string, rv.data.strip())
