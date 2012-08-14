import webapp2

from counters import Counter

class MainPage(webapp2.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(MainPage, self).__init__(*args, **kwargs)
        self.results = None
        self.name = ''

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write("""
<html>
<body>
<form method='POST'>
    <input name="name" value="%s" />
    <input type="submit" />
</form>
""" % self.name)
        if self.results:
            self.response.out.write("<table><tr><th>TS</th><th>Value</th></tr>")
            self.response.out.write('<tr><td><b>Counter</b></td><td><b>%s</b></td></tr>' % self.results['counter'])
            self.response.out.write('<tr><td><b>Min</b></td><td><b>%s</b></td></tr>' % self.results['min'])
            self.response.out.write('<tr><td><b>Max</b></td><td><b>%s</b></td></tr>' % self.results['max'])
            self.response.out.write('<tr><td><b>Avg</b></td><td><b>%s</b></td></tr>' % self.results['avg'])
            for key in sorted(self.results['data'].keys()):
                self.response.out.write('<tr><td>%s</td><td>%s</td></tr>' % (key, self.results['data'][key]))
            self.response.out.write("</table>")
        self.response.out.write("""
</body>
</html>
""")

    def post(self):
        name = self.request.params['name']
        Counter(name).tick()
        self.results = Counter(name).get_data(count=1440)
        self.name = name
        self.get()

ROUTES = [
    ('/', MainPage)
]

APP = webapp2.WSGIApplication(ROUTES)
