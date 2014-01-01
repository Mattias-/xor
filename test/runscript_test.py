#!/usr/bin/env python
import unittest
import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(".."))
from xonrequest import Xor

simple_rule = {'route': '/t1/<val1>',
        'output': True,
        'script': 'files/whoami.sh'}

class RunscriptSudoTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_run_script_as_same_user(self):
        username = subprocess.check_output(['whoami']).strip()
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        rv = client.get('/t1/cba')
        test_string = username + '\ncba'
        self.assertEqual(test_string, rv.data.strip())

    def test_run_script_as_root(self):
        rule = simple_rule.copy()
        rule.update({'user': 'root'})
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        username = subprocess.check_output(['whoami']).strip()
        if username == 'root':
            rv = client.get('/t1/cba')
            test_string = 'root\ncba'
            self.assertEqual(test_string, rv.data.strip())
        else:
            with self.assertRaisesRegexp(Exception, 'Permission denied'):
                rv = client.get('/t1/cba')

    def test_run_script_as_other_user(self):
        rule = simple_rule.copy()
        rule.update({'user': 'nobody'})
        self.x.add_rules([rule])
        client = self.x.app.test_client()
        username = subprocess.check_output(['whoami']).strip()
        if username == 'root':
            rv = client.get('/t1/cba')
            test_string = 'nobody\ncba'
            self.assertEqual(test_string, rv.data.strip())
        else:
            with self.assertRaisesRegexp(Exception, 'Permission denied'):
                rv = client.get('/t1/cba')

    def test_run_scripts_as_different_users(self):
        rule2 = simple_rule.copy()
        rule3 = simple_rule.copy()
        rule2.update({'route': '/t2/<val2>','user': 'root'})
        rule3.update({'route': '/t3/<val2>','user': 'nobody'})
        self.x.add_rules([simple_rule, rule2, rule3])
        client = self.x.app.test_client()
        username = subprocess.check_output(['whoami']).strip()
        rv = client.get('/t1/cba')
        test_string = username + '\ncba'
        self.assertEqual(test_string, rv.data.strip())
        if username == 'root':
            rv2 = client.get('/t2/cba')
            test_string2 = 'root\ncba'
            self.assertEqual(test_string2, rv2.data.strip())
            rv3 = client.get('/t3/cba')
            test_string3 = 'nobody\ncba'
            self.assertEqual(test_string3, rv3.data.strip())
        else:
            with self.assertRaisesRegexp(Exception, 'Permission denied'):
                rv = client.get('/t2/cba')
            with self.assertRaisesRegexp(Exception, 'Permission denied'):
                rv = client.get('/t3/cba')

if __name__ == '__main__':
    unittest.main()