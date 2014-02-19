import urlparse

import requests
import lxml.etree as etree


class Discover(object):
    def __init__(self, url, user=None, password=None):
        self.starturl = url
        if urlparse.urlsplit(url).scheme == '':
            url = 'https://' + url
        spliturl = urlparse.urlsplit(url)
        self.baseurl = spliturl.scheme + '://' + spliturl.hostname
        if spliturl.username:
            user = spliturl.username
        if spliturl.password:
            password = spliturl.password

        self.auth = (user, password)

        self._default_headers = {'User-Agent': 'leif 0.1'}

        self._already_checked = list()

    def find_principal(self):
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 0
        body = """<d:propfind xmlns:d="DAV:">
  <d:prop>
     <d:current-user-principal />
  </d:prop>
</d:propfind>"""
        res = requests.request('PROPFIND', self.starturl, auth=self.auth,
                               headers=headers, data=body)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))

        for element in root.iter('{*}current-user-principal'):
            for principal in element.iter():  # should be only one
                if principal.tag.endswith('href'):
                    yield principal.text

    def find_home(self, principal):
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 0
        url = self.baseurl + principal
        body = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
    <c:calendar-home-set />
  </d:prop>
</d:propfind>"""
        res = requests.request('PROPFIND', url, auth=self.auth,
                               headers=headers, data=body)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))

        for element in root.iter('{*}calendar-home-set'):
            for homeset in element.iter():
                if homeset.tag.endswith('href'):
                    yield homeset.text

    def find_calendars(self, home):
        headers = dict()
        headers.update(self._default_headers)
        headers['Depth'] = 1
        url = self.baseurl + home
        body = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
     <d:resourcetype />
     <d:displayname />
     <c:supported-calendar-component-set />
  </d:prop>
</d:propfind>"""
        res = requests.request('PROPFIND', url, auth=self.auth,
                               headers=headers, data=body)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))
        for response in root.iter('{*}response'):
            for element in response.iter():
                print element.tag, element.text
            #for homeset in element.iter():
                #if homeset.tag.endswith('href'):
                    #yield homeset.text
