"""
Tests for tick
"""
import datetime
import logging

from google.appengine.api import memcache, namespace_manager

from counters import Counter, KEY_PREFIX, GLOBAL_NS

from test.fixture import CounterTestCase

class TickTest(CounterTestCase):
    """
    Tests for Counter.tick()
    """
    def get_value_for_name_dt(self, name, dt, namespace=None):
        key = KEY_PREFIX + Counter.build_memcache_key(name, dt)
        value = memcache.get(key, namespace=namespace)
        return value

    def assert_value_for_name_dt(self, name, dt, expected_value, namespace=None):
        value = self.get_value_for_name_dt(name, dt, namespace=namespace)
        self.assertEquals(value, expected_value)

    def test_counter_ticked(self):
        name    = 'h1'
        now     = datetime.datetime.utcnow()
        counter = Counter(name, _now=now)
        counter.tick()
        counter.tick()
        counter.tick()
        self.assert_value_for_name_dt(name, now, 3)

    def test_multiple_counters_ticked(self):
        name    = 'h1:h2'
        now     = datetime.datetime.utcnow()
        counter = Counter(name, _now=now)
        counter.tick()
        counter.tick()
        self.assert_value_for_name_dt('h1', now, 2)
        self.assert_value_for_name_dt('h1:h2', now, 2)

    def test_counter_starts_at_zero(self):
        name    = 'h1'
        now     = datetime.datetime.utcnow()
        counter = Counter(name, _now=now)
        counter.tick()
        self.assert_value_for_name_dt(name, now, 1)

    def test_new_minute_starts_new_counter(self):
        name    = 'h1'
        now     = datetime.datetime.utcnow()
        later   = now + datetime.timedelta(minutes=1)
        counter = Counter(name, _now=now)
        counter.tick()
        self.assert_value_for_name_dt(name, now, 1)
        counter = Counter(name, _now=later)
        counter.tick()
        counter.tick()
        self.assert_value_for_name_dt(name, later, 2)

    def test_namespace_partitions_counter(self):
        name = 'h1'
        now     = datetime.datetime.utcnow()
        namespace_manager.set_namespace('ns1')
        counter = Counter(name, _now=now)
        counter.tick()
        self.assert_value_for_name_dt(name, now, 1, namespace='ns1')
        namespace_manager.set_namespace('ns2')
        counter = Counter(name, _now=now)
        counter.tick()
        self.assert_value_for_name_dt(name, now, 1, namespace='ns2')

    def test_ignored_namespace_ticks_global_counter(self):
        name = 'h1'
        now  = datetime.datetime.utcnow()
        namespace_manager.set_namespace('ns1')
        counter = Counter(name, ignore_namespace=True, _now=now)
        counter.tick()
        self.assert_value_for_name_dt(name, now, 1, namespace=GLOBAL_NS)
