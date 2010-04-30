#!/home/sfrazer/bin/python

from os.path import join, getsize, exists
from optparse import OptionParser
from time import time
import hashlib
import binascii
import hmac
import urllib.parse
import http.client
import sys
from xml.dom import minidom

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

class RequestGenerator:
    
    def __init__(self, api_id, secret):
        self.secret = secret
        self.api_id = api_id

    def set_url(self, url):
        url = urllib.parse.urlsplit(url)
        query = {}
        if url.query:
            for param in url.query.split('&'):
                (var, val) = param.split('=')
                query[var] = val
        
        self.url = {'scheme': url.scheme, 'netloc': url.netloc, 'path': url.path, 'query_raw': url.query, 'query': query, 'fragment': url.fragment}

    def gen_query_str(self, api_ts, urlencode=False):
        query = 'api_ver=1&api_id=' + self.api_id + '&api_ts=' + str(api_ts)
        if self.url['query_raw']:
            query = self.url['query_raw'] + '&' + query
        return query

    def gen_signing_string(self, api_ts):
        string = "\n".join([self.api_id, str(api_ts), self.url['path'], self.gen_query_str(api_ts)])
        return hmac.new(self.secret.encode(), string.encode(), hashlib.sha1).hexdigest()

    def full_url(self, url):
        unix_ts = int(time())
        self.set_url(url)
        signing_string = self.gen_signing_string(unix_ts)
        url = self.url['scheme'] + "://" + self.url['netloc'] + self.url['path'] + "?" + self.gen_query_str(unix_ts) + '&api_mac=' + signing_string
        return url

if __name__ == '__main__':
    usage = "Usage: %prog [options]"
    version = "BSD PyAPI 1.0"

    parser = OptionParser(usage=usage, version=version)

    parser.add_option("-v", "--verbose", 
                      dest="verbose",
                      help="Makes this tool loud and obnoxious.", 
                      action="store_true",
                      default=False)

    parser.add_option("-i", "--api_id",
                      dest="api_id",
                      help="The api_id", 
                      default='sfrazer')

    parser.add_option("-o", "--host",
                      dest="host",
                      help="The host", 
                      default='enoch.bluestatedigital.com')

    parser.add_option("-p", "--port",
                      dest="port",
                      help="The port", 
                      default='17260')

    parser.add_option("-s", "--secret",
                      dest="secret",
                      help="The secret",
                      default='7405d35963605dc36702c06314df85db7349613f')

    (options, args) = parser.parse_args()
 
    url = args[0]

    request = RequestGenerator(options.api_id, options.secret)

    connection = http.client.HTTPConnection(options.host, options.port)
    url_secure = request.full_url(url)

    if options.verbose:
        print(url_secure)

    connection.request('GET', url_secure)
    response = connection.getresponse()

    headers = response.getheaders()
    data = response.read().decode()
    try:
        data_xml = minidom.parseString(data)
        data_xml_formatted = data_xml.toxml()
        data_status = "%sXML Okay%s\n" % (bcolors.OKGREEN, bcolors.ENDC)
    except:
        data_xml_formatted = ''
        data_status = "%sXML Malformed%s\n" % (bcolors.FAIL, bcolors.ENDC)

    http_version = ('HTTP/1.0' if response.version == 10 else 'HTTP/1.1')
    if response.status == 200:
        color = bcolors.OKGREEN
    elif response.status == 202:
        color = bcolors.WARNING
    else:
        color = bcolors.FAIL

    sys.stdout.write("%s%s %s %s%s\n" % (color, http_version, response.status, response.reason, bcolors.ENDC))

    for (key, value) in headers:
        sys.stdout.write( "%s%s: %s%s\n" % (bcolors.HEADER, key, value, bcolors.ENDC))

    sys.stdout.write("\n%s\n\n%s\n" % (data_xml_formatted, data_status))
    connection.close()
