#!/usr/bin/env python
#-*- coding: utf-8 -*-

import httplib
import urlparse
import urllib
import json
import threading

import oauth
import status

# Streaming API Stream class
class Stream(threading.Thread):
    def __init__(self, hose):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        self.hose = hose
        self.event = threading.Event()
        self._lock = threading.Lock()
        self._buffer = unicode()
        self.start()
    
    def run(self):
        while True:
            s = unicode()
            
            while True:
                # get delimited (number of bytes that should read
                s += self.hose.read(1)
                if s.strip().find("\n") > 0: break
            
            bytes, s = s.strip().split("\n", 1)
            
            # read stream
            self._lock.acquire()
            try:
                self._buffer += s + self.hose.read(int(bytes) - len(s))
            except:
                print s
                raise
            self._lock.release()
            
            self.event.set()
            self.event.clear()
    
    # pop statuses
    def pop(self):
        self._lock.acquire()
        
        try:
            json_str, self._buffer = self._buffer.rsplit("\n", 1)
        except ValueError:
            statuses = []
        except Exception, e:
            statuses = []
            print >>sys.stderr, "[Error] %s" % e
        else:
            statuses = json.loads(u"[%s]" % json_str.replace("\n", ","))
        
        self._lock.release()
        
        return [status.twstatus(i) if "delete" not in i else i
                for i in statuses]

# Streaming API class
class StreamingAPI:
    def __init__(self, oauth):
        self.oauth = oauth
    
    def _start(self, path, params = {}):
        host = "stream.twitter.com"
        url = "http://%s%s" % (host, path)
        
        # added delimited parameter
        params["delimited"] = "length"
        
        header = { "Connection" : "keep-alive" }
        conn = self.oauth.oauth_http_request(url, "GET", params, header)
        response = conn.getresponse()
        
        if response.status != 200:
            raise httplib.HTTPException, "%s %s" % (response.status, response.reason)
        
        return response
    
    def sample(self):
        path = "/1/statuses/sample.json"
        return Stream(self._start(path))
    
    def filter(self, follow = [], locations = [], track = []):
        path = "/1/statuses/filter.json"
        
        params = dict()
        if follow:
            params["follow"] = urllib.quote(u",".join([unicode(i) for i in follow]).encode("utf-8"), ",")
        if locations:
            params["locations"] = urllib.quote(u",".join([unicode(i) for i in locations]).encode("utf-8"), ",")
        if track:
            params["track"] = urllib.quote(u",".join([unicode(i) for i in track]).encode("utf-8"), ",")
            print params["track"]
            
        return Stream(self._start(path, params))

if __name__ == "__main__":
    import sys

    ckey = sys.argv[1]
    csecret = sys.argv[2]
    atoken = sys.argv[3]
    asecret = sys.argv[4]
    
    oauth = oauth.oauth(ckey, csecret, atoken, asecret)
    
    s = StreamingAPI(oauth)
    #streaming = s.filter(locations = [-122.75,36.8,-121.75,37.8,-74,40,-73,41])
    streaming = s.sample()
    #streaming = s.filter(track = [u"spcamp", u"セプキャン"])
    
    while True:
        statuses = streaming.pop()
        for i in statuses:
            try:
                print i.user.screen_name, i.text
            except:
                print i
        
        streaming.event.wait()
