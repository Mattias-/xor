#!/usr/bin/env python
import os
import sys
import unittest

from xor import Xor

script_path = 'tests/files/'
cfg = [{'route': '/t1/<val1>',
        'output': True,
        'script': script_path+'echo.sh'},
       {'route': '/t2/<val1>/<val2>',
        'output': True,
        'script': script_path+'echo.sh'},
       {'route': '/t3/<val1>',
        'script': script_path+'echo.sh'},
       {'route': '/t4/<val1>',
        'script': 'xxxxxx'},
       {'route': '/t4out/<val1>',
        'output': True,
        'script': 'xxxxxx'},
       {'route': '/t5/<val1>',
        'output': True,
        'script': script_path+'nohashbang.sh'},
       {'route': '/t6/<val1>',
        'output': True,
        'script': script_path+'notexec.sh'}
       ]


class RunScriptWebTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_one_val(self):
        self.x.add_rules([cfg[0]])
        client = self.x.app.test_client()
        test_string = 'ddd'
        rv = client.get('/t1/' + test_string)
        self.assertEqual(test_string, rv.data.strip())

    def test_two_val(self):
        self.x.add_rules([cfg[1]])
        client = self.x.app.test_client()
        test_string = 'ddd fff'
        splitted = test_string.split()
        rv = client.get('/t2/' + splitted[0] + '/' + splitted[1])
        self.assertTrue(all([s in rv.data for s in splitted]))

    def test_no_output(self):
        self.x.add_rules([cfg[2]])
        client = self.x.app.test_client()
        rv = client.get('/t3/something')
        self.assertEqual('0', rv.data)

    def test_negative_script(self):
        self.x.add_rules([cfg[3]])
        client = self.x.app.test_client()
        rv = client.get('/t4/something')
        # exit status 127 = command not found
        #self.assertEqual('127', rv.data)
        self.assertEqual('2', rv.data)

    def test_neg_script_output_nofile(self):
        self.x.add_rules([cfg[4]])
        client = self.x.app.test_client()
        with self.assertRaisesRegexp(OSError, 'No such file'):
            rv = client.get('/t4out/something')

    def test_neg_script_output_nohashbang(self):
        self.x.add_rules([cfg[5]])
        client = self.x.app.test_client()
        with self.assertRaisesRegexp(OSError, 'Exec format error'):
            rv = client.get('/t5/something')

    def test_neg_script_output_notexec(self):
        self.x.add_rules([cfg[6]])
        client = self.x.app.test_client()
        with self.assertRaisesRegexp(OSError, 'Permission denied'):
            rv = client.get('/t6/something')

    def test_multiple_rules(self):
        self.x.add_rules(cfg)
        client = self.x.app.test_client()
        test_string1 = 'ddd'
        rv1 = client.get('/t1/' + test_string1)
        self.assertEqual(test_string1, rv1.data.strip())
        test_string2 = 'ddd fff'
        splitted = test_string2.split()
        rv2 = client.get('/t2/' + splitted[0] + '/' + splitted[1])
        self.assertTrue(all([s in rv2.data for s in splitted]))
        rv3 = client.get('/t3/something')
        self.assertEqual('0', rv3.data)
        rv4 = client.get('/t4/something')
        # exit status 127 = command not found
        #self.assertEqual('127', rv4.data)
        self.assertEqual('2', rv4.data)
        with self.assertRaisesRegexp(OSError, 'No such file'):
            rv5 = client.get('/t4out/something')
