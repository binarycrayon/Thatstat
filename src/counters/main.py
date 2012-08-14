"""
API end-points for the counters package.

To mount these end-points, add the following to your app.yaml's handlers section (Python 2.7):

    handlers:
    - url: /__counters__/.*
      script: counters.main.APP
"""
import webapp2

from .handlers import *

ROOT = '/__counters__'

ROUTES = [
    (ROOT + '/latest', LatestDataHandler),
    (ROOT + '/', HomePage),
]

APP = webapp2.WSGIApplication(ROUTES)
