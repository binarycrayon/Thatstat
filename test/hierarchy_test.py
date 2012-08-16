"""
Tests for computing the hierarchy.
"""
from counters import Counter

from test.fixture import CounterTestCase

class HierarchyTests(CounterTestCase):
    """
    Tests for parse_hierarchy().
    """
    def test_single_name_parsed(self):
        name = 'h1'
        counter = Counter(name)
        self.assertEquals(['h1'], counter.hierarchy)

    def test_double_names_parsed(self):
        name = 'h1:h2'
        counter = Counter(name)
        self.assertEquals(['h1', 'h1:h2'], counter.hierarchy)

    def test_triple_names_parsed(self):
        name = 'h1:h2:h3'
        counter = Counter(name)
        self.assertEquals(['h1', 'h1:h2', 'h1:h2:h3'], counter.hierarchy)

    def test_doubled_colons_fail(self):
        name = 'h1::h2'
        with self.assertRaises(ValueError):
            counter = Counter(name)
