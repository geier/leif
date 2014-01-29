import requests
import lxml.etree as etree


class Discover(object):
    def __init__(self, url, user=None, password=None):
        self.baseurl = url
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
        res = requests.request('PROPFIND', self.baseurl, auth=self.auth,
                               headers=headers, data=body)
        res.raise_for_status()
        root = etree.fromstring(res.text.encode('utf-8'))

        for element in root.iter('{*}current-user-principal'):
            for principal in element.iter():  # should be only one
                if principal.tag.endswith('href'):
                    yield principal.text
