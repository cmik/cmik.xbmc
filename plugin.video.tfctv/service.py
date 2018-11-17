#!/usr/bin/env python2
import SocketServer
import re
import shutil
import threading
import urllib, urllib2, ssl, cookielib
import xbmc, xbmcaddon

from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse

AddonName = xbmcaddon.Addon('plugin.video.tfctv').getAddonInfo('name')
setting = xbmcaddon.Addon().getSetting

class ProxyHandler(SimpleHTTPRequestHandler):

    _cj = cookielib.LWPCookieJar()
    _user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'
            
    def do_GET(self):
        query = self.getQueryParameters(self.path)
        if ('url' in query):
        
            requestHeaders = []
            for h in self.headers:
                if h.lower() not in ('host', 'user-agent', 'icy-metadata', 'connection'):
                    requestHeaders.append((h, self.headers.get(h)))
            requestHeaders.append(('User-Agent', self._user_agent))
            requestHeaders.append(('Connection', 'keep-alive'))
            requestHeaders.append(('Keep-Alive', 'timeout=5, max=1000'))
            
            res = self.urlopen(query.get('url'), headers=requestHeaders)
            
            if (res.get('status')):
                proxyUrlFormat = setting('proxyHostUrl')
                content = re.sub(r'(http[^\s"]+)', lambda x: proxyUrlFormat % (setting('proxyPort'), urllib.quote(x.group(0))), res.get('body'))
                
                self.send_response(res.get('status'))
                for header, value in res.get('headers').items():
                    if (header.lower() == 'content-length'):
                        value = len(content)
                    if (header.lower() == 'set-cookie'):
                        netloc = urlparse(proxyUrlFormat).netloc
                        host = netloc.split(':')[0] if ':' in netloc else netloc
                        value = re.sub(r'path=[^;]+; domain=.+', 'path=/; domain=%s' % (host), value)
                    if (header.lower() in ('server', 'set-cookie')):
                        continue
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(content)
                self.wfile.close()
            else:
                self.send_error(522)
        else:
            self.send_error(400)
                        
    def urlopen(self, url, params = {}, headers = []):        
        res = {}
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), urllib2.HTTPCookieProcessor(self._cj))
        opener.addheaders = headers
        requestTimeOut = int(xbmcaddon.Addon().getSetting('requestTimeOut')) if xbmcaddon.Addon().getSetting('requestTimeOut') != '' else 20
        response = None
        
        try:
            if params:
                data_encoded = urllib.urlencode(params)
                response = opener.open(url, data_encoded, timeout = requestTimeOut)
            else:
                response = opener.open(url, timeout = requestTimeOut)
                
            res['body'] = response.read() if response else ''
            res['status'] = response.getcode()
            res['headers'] = response.info()
            res['url'] = response.geturl()
        except (urllib2.URLError, ssl.SSLError) as e:
            message = '%s : %s' % (e, url)
            xbmc.log(message, level=xbmc.LOGERROR)
        
        return res
        
    def getQueryParameters(self, url):
        qparam = {}
        query = url.split('?')[1] if (len(url.split('?')) > 1) else None 
        if query:
            pairs = query.split('&')
            for i in range(len(pairs)):
                keyvalue = pairs[i].split('=')
                if (len(keyvalue)) == 2:
                    qparam[keyvalue[0]] = urllib.unquote(keyvalue[1])
        return qparam 
        
if __name__ == "__main__":
    httpPort = int(setting('proxyPort'))
    server = SocketServer.TCPServer(('', httpPort), ProxyHandler)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    xbmc.log('[%s] Service: starting HTTP proxy server on port %s' % (AddonName, httpPort), level=xbmc.LOGNOTICE)
    
    monitor = xbmc.Monitor()

    # XBMC loop
    while not monitor.waitForAbort(10):
        pass

    server.shutdown()
    server_thread.join()
    xbmc.log('[%s] - Service: stopping HTTP proxy server on port %s' % (AddonName, httpPort), level=xbmc.LOGNOTICE)