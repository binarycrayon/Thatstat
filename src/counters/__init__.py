"""
High-rate counters.

Counter('my-counter').tick()
Counter('my-group:my-counter-1').tick() # ticks both "my-group" and "my-group:my-counter-1"
Counter('my-group:my-counter-2').tick() # ticks both "my-group" and "my-group:my-counter-2"
"""
import os
import re
import logging
import datetime

from google.appengine.api import memcache

VALID_NAME       = r'^[a-zA-Z][a-zA-Z0-9-_:]+$'
VALID_NAME_RE    = re.compile(VALID_NAME)
KEY_PREFIX       = '__counters__'
GLOBAL_NS        = '__global__'
MINUTE_FORMAT    = '%Y%m%dT%H%M00Z'
IS_DEV_APPSERVER = os.environ.get('SERVER_SOFTWARE', 'development').lower().startswith('development')

class KEY(object):
    COUNTER = 'counter'
    MIN     = 'min'
    MAX     = 'max'
    AVG     = 'avg'
    DATA    = 'data'

class Counter(object):
    """
    A high-rate counter. Depends on memcache. If memcache is ejected, counter data will be lost.
    """
    def __init__(self, name, ignore_namespace=False, _now=None):
        """
        Initializes a counter. To tick the counter, call tick().

        Args:
            name The name of the counter. You can specify heirarchical counters by using the ":" character, e.g.,
                 "hier1:hier2:hier3". Valid counter names are [a-zA-Z][a-zA-Z0-9-_:]+
        Kwargs:
            ignore_namespace The memcache storage for counters respects the namespace_manager's current namespace by
                             default. If you want to drive your counters into a common namespace, set this value to
                             True. This can be useful when you have a multi-tennanted app, but you want to have a
                             counter that spans all tennants.
            _now             Just used for unit testing.
        """
        if not VALID_NAME_RE.match(name):
            raise ValueError('Invalid name "%s". Name must match "%s".' % (name, VALID_NAME))
        if name.find('::') >= 0:
            raise ValueError('You require at least one letter between ":" characters.')
        super(Counter, self).__init__()
        self.name = name
        self.hierarchy = self.parse_hierarchy()
        self.ignore_namespace = ignore_namespace
        self._now = _now

    def tick(self):
        """
        Ticks the counter asynchronously.
        """
        d = dict( (key, 1) for key in self.build_current_memcache_keys() )
        logging.info('Ticking %s', d)
        client = memcache.Client()
        rpc = client.offset_multi_async(d, key_prefix=KEY_PREFIX, initial_value=0, namespace=self.namespace)
        if IS_DEV_APPSERVER:
            # dev_appserver requires that you wait on an RPC in order for it to start
            rpc.wait()

    # def get_current_values(self):
    #     """
    #     Returns a dictionary of hierarchical name to value for current time interval.
    #     """
    #     keys = self.build_current_memcache_keys()
    #     client = memcache.Client()
    #     result = client.get_multi(keys, key_prefix=KEY_PREFIX, namespace=self.namespace)
    #     d = dict( (k.rpartition(':')[0], v) for k, v in result.iteritems() )
    #     return d

    def build_current_memcache_keys(self):
        """
        Builds a list of current memcache keys.
        """
        now = self._now or datetime.datetime.utcnow()
        keys = []
        for name in self.hierarchy:
            keys.append(self.build_memcache_key(name, now))
        return keys

    def get_data(self, count=30):
        """
        Returns a dictionary of 'count' data points.

        Important: unlike tick(), get_data() only returns data for a single counter. E.g., if you instantiated this
        class with 'hier1:hier2:hier3', then get_data() only returns data for that specific counter.
        To retrieve data for others, you must explicitly do:

                 Counter('hier1').get_data()
                 Counter('hier1:hier2').get_data().

        Kwargs:
            count The number of data points to retrieve. This typically is the number of intervals backwards in time to
                  retrieve (typically minutes).

        Returns a dictionary of counter results:

            {
                'counter': 'hier1:hier2',
                'min': 2,
                'max': 12,
                'avg': 3.14
                'data': {
                    '20120716T143200Z': 1,
                    '20120716T143100Z': None, # means data is missing, or none recorded
                    '20120716T143000Z': 11,
                    ... # "count" data points
                }
            }
        """
        rpc = self.get_data_async(count=count)
        rpc.wait()
        return rpc.counters

    def get_data_async(self, count=30):
        """
        Asynchronously gets counter data.

        Returns an rpc object. As a caller, you must do the following to get the result:

            counter = Counter('my-counter')
            rpc = counter.get_data_async()
            rpc.wait()
            result = rpc.counters # NOTE: the processed results are placed on rpc.counters (a non-standard location)

        Typically, you will want to retrieve a set of results in parallel (and thus the _async method). The pattern
        to do so is as follows:

            names = ['my-counter', 'my-other-counter', 'yet-another-counter']
            rpcs  = []
            for name in names:
                counter = Counter(name)
                rpc = counter.get_data_async()
                rpcs.append(rpc)

            result = []
            for rpc in rpcs:
                rpc.wait()
                result.append(rpc.counters)

        See the docstring for get_data for the shape of rpc.counters.
        """
        datetimes = self.build_datetimes(count=count)
        keys      = [self.build_memcache_key(self.name, dt) for dt in datetimes]
        rpc       = memcache.create_rpc()

        def process_result():
            """ Callback to convert the results from memcache get_multi_async. """
            counters = rpc.get_result()
            min_ = 2**15
            max_ = avg_ = sum_ = 0
            for value in counters.itervalues():
                min_ = min(value, min_)
                max_ = max(value, max_)
                sum_ += value
            if len(counters):
                avg_ = sum_ / float(len(counters))
            data = {}
            for dt, key in zip(datetimes, keys):
                value = counters.get(key, None)
                data[dt.strftime(MINUTE_FORMAT)] = value
            results = {
                KEY.COUNTER : self.name,
                KEY.MIN     : min_,
                KEY.MAX     : max_,
                KEY.AVG     : avg_,
                KEY.DATA    : data
            }
            rpc.counters = results # HACK, I would rather "get involved" in the get response hook, but this feels like
                                   # it would be difficult to forge in to the existing pattern

        rpc.callback = process_result
        client       = memcache.Client()
        rpc2         = client.get_multi_async(keys, key_prefix=KEY_PREFIX, namespace=self.namespace, rpc=rpc)
        assert rpc == rpc2
        return rpc2

    @staticmethod
    def build_memcache_key(name, dt):
        """
        Using the given counter name and datetime, builds a memcache key to rival all others.
        """
        return '%s:%s' % (name, dt.strftime(MINUTE_FORMAT))

    def build_datetimes(self, count=30):
        """
        Builds "count" datetimes starting from now and going back in time for "count" intervals (typically a minute).

        Kwargs:
            count The number of intervals to construct.
        """
        now = self._now or datetime.datetime.utcnow()
        now -= datetime.timedelta(seconds=now.second)
        now -= datetime.timedelta(microseconds=now.microsecond)
        datetimes = []
        for i in xrange(0, count):
            then = now - datetime.timedelta(minutes=i)
            datetimes.append(then)
        return datetimes

    def parse_hierarchy(self):
        """
        Parse a hierarchical name "h1:h2:h3" into ['h1', 'h1:h2', 'h1:h2:h3']
        """
        name = self.name
        colon = name.find(':')
        hierarchy = []
        while colon >= 0:
            value = name[0:colon]
            hierarchy.append(value)
            colon = name.find(':', colon+1)
        hierarchy.append(name)
        return hierarchy

    @property
    def namespace(self):
        """
        Returns the namespace for the memcache work.

        The namespace will always be the current namespace manager's namespace, unless this
        class is instantiated with ignore_namespace=True. ignore_namespace=True is useful
        when you have a multi-tennanted app, but you want to have a global counter that spans
        all tennants.
        """
        if self.ignore_namespace:
            return GLOBAL_NS
        return None
