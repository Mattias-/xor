#!/usr/bin/env python
import os
import shutil
import sys
import subprocess
import unittest
from urllib2 import quote

from xor import Xor

echo_rule = {'route': '/echo/<val1>',
        'output': True,
        'out_redir': True,
        'command': 'echo'}
cat_rule = {'route': '/cat/<var>',
        'output': True,
        'in_redir': True,
        'command': 'cat'}
tr_rule = {'route': '/tr/<v1>/<v2>',
           'output': True,
           'out_redir': True,
           'in_redir': True,
           'command': 'tr'}

IO_DIR = 'tests/io_tmp'

class IOTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True
        if not os.path.exists(IO_DIR):
          os.mkdir(IO_DIR)

    def tearDown(self):
        shutil.rmtree(IO_DIR)

    def test_echo_out(self):
        self.x.add_rules([echo_rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/echo_out.txt'
        test_string = 'Hello World'
        rv = client.get('/echo/%s?>=%s' % (test_string, file_name))
        self.assertEqual('0', rv.data.strip())
        self.assertEqual(test_string, open(file_name).read().strip())

    def test_echo_out_no_redir(self):
        rule = echo_rule.copy()
        rule.pop('out_redir')
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/echo_out.txt'
        test_string = 'Hello World'
        rv = client.get('/echo/%s?>=%s' % (test_string, file_name))
        self.assertEqual('>=%s %s' % (file_name, test_string), rv.data.strip())
        self.assertFalse(os.path.exists(file_name))

    def test_echo_out_false_redir(self):
        rule = echo_rule.copy()
        rule['out_redir'] = False
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/echo_out.txt'
        test_string = 'Hello World'
        rv = client.get('/echo/%s?>=%s' % (test_string, file_name))
        self.assertEqual('>=%s %s' % (file_name, test_string), rv.data.strip())
        self.assertFalse(os.path.exists(file_name))

    def test_cat_in(self):
        self.x.add_rules([cat_rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/cat_in.txt'
        test_string = 'Hello World'
        with open(file_name, 'w') as file:
            file.write(test_string)
        rv = client.get('/cat/%s?<=%s' % ('-', file_name))
        self.assertEqual(test_string, rv.data.strip())

    def test_cat_in_no_redir(self):
        rule = cat_rule.copy()
        rule.pop('in_redir')
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/cat_in.txt'
        test_string = 'Hello World'
        with open(file_name, 'w') as file:
            file.write(test_string)
        rv = client.get('/cat/%s?<=%s' % (' ', file_name))
        self.assertIn('No such file', rv.data.strip())

    def test_cat_in_false_redir(self):
        rule = cat_rule.copy()
        rule['in_redir'] = False
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/cat_in.txt'
        test_string = 'Hello World'
        with open(file_name, 'w') as file:
            file.write(test_string)
        rv = client.get('/cat/%s?<=%s' % (' ', file_name))
        self.assertIn('No such file', rv.data.strip())

    def test_cat_require_in(self):
        rule = cat_rule.copy()
        rule['require_in_redir'] = True
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/cat_in.txt'
        test_string = 'Hello World'
        with open(file_name, 'w') as file:
            file.write(test_string)
        with self.assertRaises(Exception):
          rv = client.get('/cat/%s' % ' ')

    def test_cat_file(self):
        self.x.add_rules([cat_rule])
        client = self.x.app.test_client()
        file_name = IO_DIR + '/cat_in.txt'
        test_string = 'Hello World'
        with open(file_name, 'w') as file:
            file.write(test_string)
        print quote(file_name, '')
        rv = client.get('/cat/ ?%s' % quote(file_name, ''))
        self.assertEqual(test_string, rv.data.strip())

    def test_tr_in_out(self):
        self.x.add_rules([tr_rule])
        client = self.x.app.test_client()
        file_name_in = IO_DIR + '/tr_in.txt'
        test_string = 'H1e2l3l4o W5o6r7l8d'
        with open(file_name_in, 'w') as file:
            file.write(test_string)
        file_name_out = IO_DIR + '/tr_out.txt'
        test_string2 = 'H_e_l_l_o W_o_r_l_d'
        rv = client.get('/tr/[:digit:]/"_"?<=%s&>=%s' %
                        (file_name_in, file_name_out))
        self.assertEqual('0', rv.data.strip())
        self.assertEqual(test_string2, open(file_name_out).read().strip())
