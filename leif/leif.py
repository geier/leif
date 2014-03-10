import urlparse

import requests
import lxml.etree as etree


class Discover(object):

    xml_home = ''
    xml_collection = ''

    str_homeset = ''

    def __init__(self, url, user=None, password=None, ssl_verify=True):
        """
        :param url: the base url from which to start discovery, if no scheme
                    ('http://' or 'https://') is given, https will be used
        :type url: unicode
        :param user: the username, if a username is part of the url,
                     this one is discarded
        :type user: unicode
        :param password: password used for authentication, if a password
                         is part of the url, this one is discarded
        :type password: unicode
        :param ssl_verify: how to verify SSL/TLS connections, passed through
                           to requests,
                           * if True will do normal certificate verification
                             with the default CA bundle,
                           * if set to a string it will try to import the file
                             at the string's location as a CA bundle,
                           * if set to False no certificate verification
                             whatsoever will be done
        :type ssl_verify: unicode/bool
        """

        if urlparse.urlsplit(url).scheme == '':
            url = 'https://' + url
        self.starturl = url
        spliturl = urlparse.urlsplit(url)
        self.baseurl = spliturl.scheme + '://' + spliturl.netloc

        if spliturl.username:
            user = spliturl.username
        if spliturl.password:
            password = spliturl.password

        self.auth = (user, password)
        self.settings = {'verify': ssl_verify}
        self._default_headers = {'User-Agent': 'leif 0.1'}

    def _find_principal(self):
        """tries to find the principal URL of the user
        :returns: iterable (but should be only of element) of urls
        :rtype: iterable(unicode)

        """
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 0
        body = """<d:propfind xmlns:d="DAV:">
  <d:prop>
     <d:current-user-principal />
  </d:prop>
</d:propfind>"""
        res = requests.request('PROPFIND', self.starturl, auth=self.auth,
                               headers=headers, data=body, **self.settings)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))

        for element in root.iter('{*}current-user-principal'):
            for principal in element.iter():  # should be only one
                if principal.tag.endswith('href'):
                    yield principal.text

    def discover(self):
        """discover all the user's CalDAV or CardDAV collections on the server
        :returns: a list of the user's collections (as urls)
        :rtype: list(unicode)
        """
        collections = list()
        for principal in self._find_principal():
            for home in self._find_home(principal):
                for collection in self._find_collections(home):
                    collections.append(collection)
        return collections

    def _find_home(self, principal):
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 0
        url = self.baseurl + principal
        res = requests.request('PROPFIND', url, auth=self.auth,
                               headers=headers, data=self.xml_home)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))

        for element in root.iter(self.str_homeset):
            for homeset in element.iter():
                if homeset.tag.endswith('href'):
                    yield homeset.text

    def _find_collections(self, home):
        raise NotImplementedError()


class CalDiscover(Discover):

    xml_home = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
    <c:calendar-home-set />
  </d:prop>
</d:propfind>"""
    xml_collection = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
     <d:resourcetype />
     <d:displayname />
     <c:supported-calendar-component-set />
  </d:prop>
</d:propfind>"""
    str_homeset = '{*}calendar-home-set'

    def _find_collections(self, home):
        """find all CalDAV collections under `home`"""

        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 1
        url = self.baseurl + home
        res = requests.request('PROPFIND', url, auth=self.auth,
                               headers=headers, data=self.xml_collection)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))
        for response in root.iter('{*}response'):
            calendar = dict()
            calendar['href'] = response.find('{*}href').text
            prop = response.find('{*}propstat/{*}prop')
            if prop.find('{*}displayname') is not None:
                calendar['displayname'] = prop.find('{*}displayname').text
            else:
                calendar['displayname'] = ''

            if prop.find('{*}resourcetype/{*}calendar') is not None:
                calendar['type'] = 'calendar'
            else:
                calendar['type'] = None

            calendar_components = prop.find('{*}supported-calendar-component-set')

            if calendar_components is not None:
                for one in calendar_components:
                    calendar[one.get('name')] = True

            if calendar['type']:
                yield calendar


class CardDiscover(Discover):
    xml_home = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <c:addressbook-home-set />
  </d:prop>
</d:propfind>"""
    xml_collection = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:cardav">
  <d:prop>
     <d:resourcetype />
     <c:addressbook />
  </d:prop>
</d:propfind>"""
    str_homeset = '{*}addressbook-home-set'

    def _find_collections(self, home):
        """find all CardDAV collections under `home`"""
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 1
        url = self.baseurl + home
        res = requests.request('PROPFIND', url, auth=self.auth,
                               headers=headers, data=self.xml_collection)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))
        for response in root.iter('{*}response'):
            calendar = dict()
            calendar['href'] = response.find('{*}href').text
            prop = response.find('{*}propstat/{*}prop')
            if prop.find('{*}displayname') is not None:
                calendar['displayname'] = prop.find('{*}displayname').text
            else:
                calendar['displayname'] = ''
            if prop.find('{*}resourcetype/{*}addressbook') is not None:
                yield calendar


if __name__ == "__main__":
    import getpass
    import sys
    url = raw_input('URL: ')
    user = raw_input('Username: ')
    password = getpass.getpass('Password: ')
    try:
        discoverer = CalDiscover(url, user, password)
        calendars = discoverer.discover()
        discoverer = CardDiscover(url, user, password)
        abooks = discoverer.discover()

    except requests.exceptions.SSLError:
        print("SSL verification failed")
        ssl_verify = raw_input("path to SSL cert bundle (see notes): ")
        if ssl_verify == 'False':
            ssl_verify = False
            cont = raw_input("SSL verification disabled, are you sure you"
                             "want to continue?[y/N] ")
            if cont != 'y':
                sys.exit("aborting...")

        discoverer = CalDiscover(url, user, password, ssl_verify)
        calendars = discoverer.discover()
        discoverer = CardDiscover(url, user, password, ssl_verify)
        abooks = discoverer.discover()

    if calendars == list() and abooks == list():
        sys.exit("Found nothing, sorry...")

    for collections, name in [(calendars, 'CalDAV'), (abooks, 'CardDAV')]:
        if collections == list():
            continue
        print("Found the following {0} resources:".format(name))

        for collection in collections:
            print(u"{name}: {base}{collection}".format(
                name=collection['displayname'],
                base=discoverer.baseurl,
                collection=collection['href'])
            )
