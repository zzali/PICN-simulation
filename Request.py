# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 09:39:38 2016

@author: Zeinab Zali
"""

class Request(object):
    def __init__(self, requestID, requesterIP, reqURL, reqTimestamp, reqResponseLen):
        self.reqID = requestID
        self.clientIP = requesterIP
        self.URL = reqURL
        self.timestamp = reqTimestamp
        self.responseLen = reqResponseLen
        self.responseTime = 0
        self.provider = None


    #Provider: {peer or rpeer (remote peer) or webserver}
    def setProvider(self,provider):
        self.provider = provider
        
    def updateResponseTime(self,time):
        self.responseTime = time