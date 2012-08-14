"""
Initialization tests.
"""
from counters import Counter

from test.fixture import CounterTestCase

class InitializationTests(CounterTestCase):
    """
    Tests of Counter.__init__
    """
    def test_must_start_with_letter(self):
        with self.assertRaises(ValueError):
            Counter('0abc')

    def test_invalid_character_raises_exception(self):
        with self.assertRaises(ValueError):
            Counter('ab*c')
        with self.assertRaises(ValueError):
            Counter('a(b)c')
        with self.assertRaises(ValueError):
            Counter('a,b,c')
        with self.assertRaises(ValueError):
            Counter('a"b"c')

    def test_hierarchical_name_okay(self):
        Counter('a:b:c')
