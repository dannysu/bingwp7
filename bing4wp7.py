import cgi
import webapp2
import datetime
import os
import urllib2
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class Image(db.Model):
    data = db.BlobProperty(required=True)
    country = db.StringProperty(required=True)
    date = db.DateProperty(required=True)
    credit = db.StringProperty(required=True)

class Pacific_tzinfo(datetime.tzinfo):
    """Implementation of the Pacific timezone."""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-8) + self.dst(dt)

    def _FirstSunday(self, dt):
        """First Sunday on or after dt."""
        return dt + datetime.timedelta(days=(6-dt.weekday()))

    def dst(self, dt):
        # 2 am on the second Sunday in March
        dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
        # 1 am on the first Sunday in November
        dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

        if dst_start <= dt.replace(tzinfo=None) < dst_end:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(hours=0)

    def tzname(self, dt):
        if self.dst(dt) == datetime.timedelta(hours=0):
            return "PST"
        else:
            return "PDT"

class MainPage(webapp2.RequestHandler):
    def get(self):

        year = self.request.get('y')
        month = self.request.get('m')
        date = self.request.get('d')

        requested_date = datetime.datetime.now(Pacific_tzinfo()).date()
        if year != '' and month != '' and date != '':
            requested_date = datetime.date(int(year), int(month), int(date))

        prev_date = requested_date - datetime.timedelta(days=1)

        images = Image.all().filter("date =", requested_date)

        display_images = []

        for image in images:
            display_images.append({
                'id': len(display_images) + 1,
                'column': 'a' if len(display_images) % 2 == 0 else 'b',
                'url': '/image/'+image.country+'/'+image.date.strftime('%Y-%m-%d')+'.jpg',
                'credit': urllib2.unquote(image.credit),
                'data': image.data
            })

        # Figure out if there are stored images from previous date
        images = Image.all().filter("date =", prev_date)

        template_values = {
            'show_previous': 'true' if images.count() > 0 else 'false',
            'previous_url': '?y='+prev_date.strftime('%Y')+'&m='+prev_date.strftime('%m')+'&d='+prev_date.strftime('%d'),
            'images': display_images,
        }

        self.response.headers["Content-Type"] = "text/html"
        self.response.headers.add_header("Expires", "Thu, 01 Dec 1994 16:00:00 GMT")
        self.response.headers.add_header("Cache-Control", "no-cache, must-revalidate")

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class ImageHandler(webapp2.RequestHandler):
    def get(self, country, year, month, date, format):
        if format != 'jpg':
            self.error(404)
            return

        requested_date = datetime.date(int(year), int(month), int(date))
        images = Image.all().filter("date =", requested_date).filter("country =", country)
        if images.count() != 1:
            self.error(404)
            return

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(images[0].data)

class Crawler(webapp2.RequestHandler):
    urlFormat = "http://appserver.m.bing.net/BackgroundImageService/TodayImageService.svc/GetTodayImage?dateOffset=-{0!s}&urlEncodeHeaders=true&osName=windowsphone&osVersion=7.0&orientation=480x800&deviceName=windowsphone&mkt={1}";
    countries = ["en-us", "en-au", "en-ca", "en-gb", "en-nz", "ja-jp", "zh-cn", "de-de"]

    def fetch(self, country):
        url = self.urlFormat.format(0, country)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return result
        else:
            return False

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        today = datetime.datetime.now(Pacific_tzinfo()).date()

        for country in self.countries:
            images = Image.all().filter("date =", today).filter("country = ", country)
            if images.count() == 1:
                continue

            result = self.fetch(country)
            if result == False:
                # Try again if first time fails
                result = self.fetch(country)

            if result != False:
                # Don't store duplicate images
                images = Image.all().filter("date =", today)

                found = False
                for image in images:
                    if image.data == result.content:
                        found = True
                        break

                if found:
                    self.response.out.write('dup: ' + country + '\n')
                    continue

                credit = ''
                for header in result.headers:
                    key = header
                    if key == 'image-info-credit':
                        value = result.headers[key]
                        credit = value

                image = Image(country=country,
                              date=today,
                              data=result.content,
                              credit=value)
                image.put()

                self.response.out.write('saved: ' + country + '\n')

app = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/image/([a-z]{2}-[a-z]{2})/([0-9]{4})-([0-9]{2})-([0-9]{2}).([a-z]*)', ImageHandler),
        ('/fetch', Crawler)
    ],
    debug=True)
