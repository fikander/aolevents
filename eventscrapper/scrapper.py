

STANDALONE = False

if not STANDALONE:
    from django.contrib.auth.models import User
    from django.contrib.sites.models import Site
    from django.conf import settings    
    from google.appengine.ext import db



# third party
from BeautifulSoup import BeautifulSoup
from googlemaps.googlemaps import GoogleMaps, GoogleMapsError

import sys, os
import codecs
import urllib2
import hashlib
import datetime



if STANDALONE:

    def backup_or_get_file(url, filename):
        if os.path.isfile(filename):
            f = open(filename, 'r')
            data = f.read()
            f.close()
        else:
            page = urllib2.urlopen(url)
            data = page.read()
            f = open(filename, 'w')
            f.write(data)
            f.close()
        return data

    class Event:
        @staticmethod
        def all():
            return Event
        @staticmethod
        def filter(a, b):
            return []

else:
    from events.models import Event, Country

class Scrapper:

    def run(self, url):
        log = ''
        # get data
        if STANDALONE:
            data = backup_or_get_file(url, '/tmp/scrapper.htm')
        else:
            page = urllib2.urlopen(url)
            data = page.read()
        # scrap it
        soup = BeautifulSoup.BeautifulSoup(data)

        results = self._scrap(soup)

        for r in results:
            checksum = self.__getChecksum(r)

            # for every result check if it already exists
            if len(Event.all().filter('checksum =', checksum)) == 0:
                # create event objects if it doesnt
                new_event = self._createEvent(r, checksum, url)
                # if new_Event is None it means results were not enough to create it
                # save to log so that we can email it later
                if new_event:
                    new_event.put()
                    log += 'Created new event %s:\n %s\n' % (new_event.get_absolute_url(), new_event)
                else:
                    log += 'Failed to create event from %s\n'%r

        # email the log now
        if not STANDALONE:
            #import email
            #email.send_email(log)
            pass
        else:
            print log
        return log

    def __getChecksum(self, r):
        m = hashlib.md5()
        keys = r.keys()
        keys.sort()
        for elem in keys:
            elem_ascii = elem.encode('utf-8')
            r_elem_ascii = r[elem].encode('utf-8')
            m.update(elem_ascii)
            m.update(r_elem_ascii)
        return m.hexdigest()


    def _scrap(self, soup):
        '''page - BeautifulSoup object'''
        raise "Not implemented"
        return [{}]


    def _createEvent(self, result, checksum, url):
        print result, '\n'
        return None




#<table cellspacing="0" border="0" class="displaylist" width="500">
#<tr><td bgcolor="#99cc99" class="displaylisttitle"><a name="Slough"></a>
#<strong>Slough (Part I)</strong></td></tr>
#<tr><td class="displaylist"> 
#<p><strong>Dates</strong> <br> Tuesday 22nd Sept 2009 - Saturday 26th Sept 2009 </p>
#<p><strong>Times</strong> <br> Weekdays: 7.00pm - 9.00pm / Weekend: 10.00am - 3.00pm</p>
#<p><strong>Venue</strong> <br> 37 Pitts road Slough SL1 3XG </p>
#<p><strong>Cost</strong> <br>&pound;200 (Student & Seniors &pound;140)</p>
#<p><strong>To register</strong> <br> Reshma: 07834 571 904 / <a href="mailto:reshnamas@yahoo.co.in">reshnamas@yahoo.co.in</a> 
#</p>
#</table>


class UKScrapper(Scrapper):

    def _scrap(self, soup):
        '''page - BeautifulSoup object'''

        results = []

        tables = soup.findAll('table', attrs={'class': 'displaylist'})
        for t in tables:
            result = {}

            city = t.find('td', attrs={'class': 'displaylisttitle'})

            try:
                result['name'] = city.find('a')['name']
            except KeyError:
                result['name'] = 'no name found'
            result['name_long'] = city.find('strong').string


            row2 = t.find('td', attrs='displaylist')
            pAll = row2.findAll('p')
            for p in pAll:
                header = p.find('strong')
                #print header
                thing = header
                if thing and header.string:
                    contents = ''
                    while (thing.nextSibling):
                        thing = thing.nextSibling
                        if thing.string:
                            contents += thing.string.strip()
                    result[header.string.lower()] = contents

            results.append(result)

        return results

    def _createEvent(self, result, checksum, url):
        REQUIRED_PARAMETERS = ['dates', 'name', 'name_long', 'venue', 'times', 'to register', 'cost']
        for p in REQUIRED_PARAMETERS:
            if not (result.has_key(p) and result[p] != ''):
                return None

        if not STANDALONE:
            admin_user = User.get_by_key_name('admin')
            if not admin_user:
                raise "Missing admin user"
            country = Country.get_by_key_name('GB')

            site = Site.objects.get_current()
            gmaps = GoogleMaps(api_key = settings.GOOGLE_MAPS_API_KEY,
                               referrer_url = site.domain)
            address = "%s, %s, GB" % (result['venue'], result['name'])
            try:
                lat, lng = gmaps.address_to_latlng(address)
            except GoogleMapsError:
                lat, lng = gmaps.address_to_latlng('GB')

            new_event = Event(active = False,
                              moderated = False,
                              name = str(result['name_long']),
                              creator = admin_user,
                              type = 22,
                              location = db.GeoPt(lat, lng),
                              country = country,
                              region = None,
                              address = str(result['venue']),
                              description = str(result),
                              free = False,
                              fees = str(result['cost']),
                              date_start = datetime.datetime.today(),
                              date_end = datetime.datetime.today(),
                              recurrent = False,
                              featured_priority = 0,
                              source_url = url,
                              source_checksum = checksum)
            return new_event
        else:
            print result, '\n'
            return None


if __name__ == "__main__":
    scrapper = UKScrapper()
    scrapper.run("http://artoflivinglondon.org/courses_inyourarea.htm")

