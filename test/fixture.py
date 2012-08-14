"""
Unittest fixtures.
"""
import unittest

from google.appengine.ext import testbed

class CounterTestCase(unittest.TestCase):

    def setUp(self):
        super(CounterTestCase, self).setUp()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        super(CounterTestCase, self).tearDown()
        self.testbed.deactivate()
