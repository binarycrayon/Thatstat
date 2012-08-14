import json

import webapp2

from . import Counter

__all__ = ['HomePage', 'LatestDataHandler']

class HomePage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('counters end-points are configured correctly.')
        return

class LatestDataHandler(webapp2.RequestHandler):
    """
    /__counters__/latest?counter=my-group:my-counter-2&counter=my-group&num=30
    [
        {
            "counter": "my-group:my-counter-2",
            "min": 2,
            "max": 22,
            "avg": 13.0,
            "data": {
                "20120715T171700Z": 12,
                "20120715T171600Z": 11,
                "20120715T171500Z": 18,
                "20120715T171400Z": 2,
                "20120715T171300Z": 22,
            }
        },
        {
            "counter": "my-group",
            "min": 2,
            ...
        }
    ]
    """

    def get(self):
        names = self.request.get_all('counter')
        if not names:
            self.response.set_status(400)
            self.response.out.write('parameter "counter" is required.')
            return
        num = int(self.request.params.get('num', 60*24))

        rpcs = []
        for name in names:
            counter = Counter(name)
            rpc = counter.get_data_async(count=num)
            rpcs.append(rpc)

        result = []
        for rpc in rpcs:
            rpc.wait()
            result.append(rpc.counters)

        data_json = json.dumps(result)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(data_json)
        return
