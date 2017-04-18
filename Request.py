# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 09:39:38 2016

@author: Zeinab Zali
"""

class Request(object):
  
    def __init__(self, requestID, reqTimestamp, latency, requesterIP, serverIP, reqURL, 
                 reqResponseLen, rtt, bw, proxy_provider):
        self.reqID = requestID
        self.clientIP = requesterIP
        self.serverIP = serverIP
        self.URL = reqURL
        self.timestamp = reqTimestamp
        self.TransferedLen = reqResponseLen + 30 + 64*(reqResponseLen/65535)   #add req size +  (Eth+IP+TCP headers)
        self.responseLen = reqResponseLen
        self.proxy_provider = proxy_provider
        self.latency = latency
        self.rtt = rtt
        self.bw = bw

    #Provider: {peer or rpeer (remote peer) or webserver}
    def setProvider(self,provider):
        self.proxy_provider = provider
        
#    def updateResponseTime(self,time):
#        self.responseTime = time