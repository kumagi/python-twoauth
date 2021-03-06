#!/usr/bin/env python
#-*- coding: utf-8 -*-

import urllib2
import urlparse
import urllib
import json
import threading

import oauth
import status

# Streaming API Stream class
class Stream(threading.Thread):
    def __init__(self, request, keepconn = True):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.request = request
        self._keep = keepconn
        
        self.die = False
        self._buffer = unicode()
        self._lock = threading.Lock()
        self.event = threading.Event()
    
    def run(self):
        hose = urllib2.urlopen(self.request)
        
        while not self.die:
            delimited = unicode()
            
            # tooooooooo slow (maybe readline() has big buffer)
            #while delimited == "":
            #    delimited = hose.readline().strip()
            
            # get delimited (number of bytes that should be read
            while not (delimited != "" and c == "\n"):
                c = hose.read(1)
                delimited += c.strip()
                
                # broken streaming hose?
                if c == "":
                    hose.close()
                    if self._keep:
                        delimited = unicode()
                        hose = urllib2.urlopen(self.request)
                        continue
                    else: return
                
                # destroy
                if self.die:
                    hose.close()
                    return
            
            bytes = int(delimited)
            
            # read stream
            self._lock.acquire()
            self._buffer += hose.read(bytes)
            self._lock.release()
            
            self.event.set()
            self.event.clear()
        
        # connection close before finish thread
        hose.close()
    
    def read(self):
        json_str = None
        
        self._lock.acquire()
        try:
            json_str, self._buffer = self._buffer.rsplit("\n", 1)
        except ValueError:
            pass
        except Exception, e:
            print >>sys.stderr, "[Error] %s" % e
        finally:
            self._lock.release()
        
        return json_str
    
    # pop statuses
    def pop(self):
        data = self.read()
        if data == None: return []
        
        return [status.twstatus(i) if "text" in i.keys() else i
                for i in json.loads(u"[%s]" % data.strip().replace("\n", ","))]
    
    def stop(self):
        self.die = True

# Streaming API class
class StreamingAPI:
    def __init__(self, oauth):
        self.oauth = oauth
    
    def _request(self, path, method = "GET", params = {}):    
        # added delimited parameter
        params["delimited"] = "length"
        req = self.oauth.oauth_request(path, method, params)
        
        return req
    
    def sample(self):
        path = "http://stream.twitter.com/1/statuses/sample.json"
        return Stream(self._request(path))
    
    def filter(self, follow = [], locations = [], track = []):
        path = "http://stream.twitter.com/1/statuses/filter.json"
        
        params = dict()
        if follow:
            params["follow"] = urllib.quote(u",".join([unicode(i) for i in follow]).encode("utf-8"), ",")
        if locations:
            params["locations"] = urllib.quote(u",".join([unicode(i) for i in locations]).encode("utf-8"), ",")
        if track:
            params["track"] = urllib.quote(u",".join([unicode(i) for i in track]).encode("utf-8"), ",")
        
        return Stream(self._request(path, "POST", params))
    
    def user(self, **params):
        path = "https://userstream.twitter.com/2/user.json"
        return Stream(self._request(path, params = params))

if __name__ == "__main__":
    import sys

    ckey = sys.argv[1]
    csecret = sys.argv[2]
    atoken = sys.argv[3]
    asecret = sys.argv[4]
    
    oauth = oauth.oauth(ckey, csecret, atoken, asecret)
    
    s = StreamingAPI(oauth)
    streaming = s.user()
    
    streaming.start()
    
    while True:
        statuses = streaming.pop()
        for i in statuses:
            try:
                print i.user.screen_name, i.text
            except:
                print i
        
        if raw_input() == "q":
            streaming.stop()
            break
