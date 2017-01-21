# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 16:30:59 2016

@author: Zeinab Zali
"""
from __future__ import print_function
import fnss
import itertools
import random
import networkx as nx
from collections import defaultdict
from Results import Results
from Request import Request
import os


class Topology(object):
    
    #each two seekers are neighbors with the probability of 1/seeker_neighbor_prob
    #n_seekers: number of local networks
    #n_hosts: total number of hosts
    #n_switches: number of switches for each local network
    def __init__(self, n_seekers, n_switches, n_hosts, seeker_neighbor_prob,
                 aliveProb, cache_policy):
        if cache_policy=='full_redundant':
            self.register = self.register_fullRedundant
        elif cache_policy=='no_redundant':
            self.register = self.register_noRedundant
        else:
            self.register = self.register_popularityBased
        self.cache_policy = cache_policy
        self.clientIDs = dict()
        #self.arrivalTimes = IPs_timestamp
        self.aliveProb = aliveProb/float(100)
        #self.tcp_size = 64*(10**3)*8#64KB
        self.bw_p2p_upload_layer1 = float(70)#Mbps
        self.bw_p2p_upload_layer2 = float(60)#Mbps
        
        self.bw_p2p_remote_upload = float(40)#Mbps
        #seek packet len = headeLen+dataLen=(4*16)+16
        self.bw_client_seeker = float(100)#10Mb/s 
        self.bw_seeker_seeker = float(100)#3Mb/s

        self.bw_client_pserver = float(50)
        self.bw_pserver_upload = float(800)
        self.bw_pserver_download = float(10)
        
               
        self.delay_client_pserver = 0.5*1000
        self.delay_client_seeker = 0.5*1000#7ms=7*1000us
 
        self.delay_seeker_seeker = 10*1000#18ms=18*1000us
        
        self.delay_p2p_layer1 = 0.25*1000#0.1ms=0.1*1000us
        self.delay_p2p_layer2 = 0.5*1000#0.1ms=0.1*1000us
        self.delay_p2p_remote = 10*1000#18ms=18*1000us
        
        #seek_msg_len = udp_header_len+msg_len=8Byte+(contentID+msgType)=8*8+1*8=9 Byte
        #seek_found_len = udp_header_len + msg_len = 8Byte+(contentID+msgType+peerID)=8*8+1*8=9 Byte
        #seek_notfound_len = udp_header_len + msg_len = 8Byte+(contentID+msgType)=8*8+1*8=9Byte
        #UDP header size = 52Byte
        self.seek_client_seeker_time = self.delay_client_seeker#+(52*8+9*8)/self.bw_client_seeker
        self.seek_seeker_seeker_time = self.delay_seeker_seeker#+(52*8+9*8)/self.bw_seeker_seeker
        #seek response packet len = headeLen+dataLen=(4*16)+5*8
        self.seekResponse_client_seeker_time = self.delay_client_seeker#+(52*8+9*8)/self.bw_client_seeker
        self.seekResponse_seeker_seeker_time = self.delay_seeker_seeker#+(52*8+9*8)/self.bw_seeker_seeker
        
        self.request_pserver_time = self.delay_client_pserver+(8000*8)/self.bw_client_pserver
        
        self.httpHEAD_req_len = 1000*8
        self.httpHEAD_response_len = 8000*8
        
        
        self.host_MaxCacheSize = 1 * 1000000000 * 8 #1GB
        self.pserver_MaxCacheSize = 200 * 1000000000 * 8 #200GB
        
        self.localPeer_foundnum = 0
        self.remotePeer_foundnum = 0
        self.notFoundnum = 0
        self.local_foundnum = 0
        self.local_foundnum_CDN = 0
        self.deniedPeerDL = 0
        self.CDN_Hit = 0
        self.CDN_miss = 0
       
        outputPath = './output/dynamic_'+str(aliveProb)+'_'+self.cache_policy+'/'
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)        
        self.f = open(outputPath+'log.txt','w')
              
        #an object for logging results
        self.results = Results(outputPath)
        self.results.initializeFiles()
        
        n_hosts_for_each_switch = (n_hosts/n_seekers)/(n_switches)+1
        self.topologyGraph = fnss.two_tier_topology(n_seekers, n_switches*n_seekers, n_hosts_for_each_switch)
        #remove all the core nodes and its links and add seeker neighbors
        tiers_type = nx.get_node_attributes(self.topologyGraph,'tier')
        #adding lookup table to seekers (tier=core)
        #print (tiers_type)
        self.seeker_nodes = [node for node in tiers_type
                             if tiers_type[node] == 'core']
                                        
        #node['lookupTable']=[('URL1',node1,node2,...),('URL2',node1,node2,...),...]
        for node in self.seeker_nodes:
            self.topologyGraph.node[node]['lookupTable'] = defaultdict(list)
            self.topologyGraph.node[node]['cache'] = []
            self.topologyGraph.node[node]['cacheSize'] = 0
            self.topologyGraph.node[node]['ip']=""
            self.topologyGraph.node[node]['available_uploadBW'] = self.bw_client_pserver
            self.topologyGraph.node[node]['available_downloadBW'] = self.bw_pserver_download
            #list of correspondig p2p upload sessions
            self.topologyGraph.node[node]['upload_sessions'] = []            
            self.topologyGraph.node[node]['download_sessions'] = []     
            
            
        #adding cache size to hosts and replacement policy (tier=leaf)
        self.host_nodes = [node for node in tiers_type
                           if tiers_type[node] == 'leaf']
                               
        for node in self.host_nodes:
            self.topologyGraph.node[node]['cache'] = []
            self.topologyGraph.node[node]['cdn_cache'] = []
            self.topologyGraph.node[node]['cacheSize'] = 0
            self.topologyGraph.node[node]['cdn_cacheSize'] = 0
            self.topologyGraph.node[node]['ip']=""
            self.topologyGraph.node[node]['available_uploadBW_s1'] = self.bw_p2p_upload_layer1
            self.topologyGraph.node[node]['available_uploadBW_s2'] = self.bw_p2p_upload_layer2
            self.topologyGraph.node[node]['available_remote_uploadBW'] = self.bw_p2p_remote_upload
            #list of correspondig p2p upload sessions
            self.topologyGraph.node[node]['upload_sessions_s1'] = []            
            self.topologyGraph.node[node]['upload_sessions_s2'] = []            
            self.topologyGraph.node[node]['upload_remote_sessions'] = []   
            self.topologyGraph.node[node]['upload_pserver_sessions'] = 0
            
        #add random neighbors for each seeker
        for pairs in itertools.combinations(self.seeker_nodes,2):
            if random.random()<1/float(seeker_neighbor_prob):
                self.topologyGraph.add_edge(pairs[0],pairs[1],type='edge_edge')
        
        self.switch_nodes = [node for node in tiers_type
                            if tiers_type[node] == 'edge']        
        #remove extra links between seekers and switches so that each seeker is connected to only n_switches switches
        
        for seeker in self.seeker_nodes:
            for switch in self.switch_nodes:
                self.topologyGraph.remove_edge(seeker,switch)
        i = 0        
        for seekerID in range(n_seekers):
            for switchID in range(i,n_switches*(seekerID+1)):
                self.topologyGraph.add_edge(self.seeker_nodes[seekerID],self.switch_nodes[switchID])
            i = n_switches*(seekerID+1)
            if i>=n_switches*n_seekers:
                break
   
    def checkPserver_uploadSessions(self,timestamp,seekerID):
        if len(self.topologyGraph.node[seekerID]['upload_sessions'])>1:
            #print len(self.topologyGraph.node[seekerID]['upload_sessions'])
            print ('shared BW for pserver upload ='+str(self.topologyGraph.node[seekerID]['upload_sessions'][0]['BW']),file=self.f)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            while i <len(self.topologyGraph.node[seekerID]['upload_sessions']):
                s = self.topologyGraph.node[seekerID]['upload_sessions'][i]
                #print s['URL']
                #computing estimated time for finishing the download with last BW value            
                #t = len/bw + (len/c+1)*d
                remainedSize = s['total_size']-s['retreived_size']
                t = remainedSize/float(s['BW'])+s['delay']
                tfinished_time = t+s['last_time']
                #print 'BW in pserver upload= ' + str(s['BW'])
#                print 'remainedSize= ' + str(remainedSize)
#                print 'totSize= ' + str(s['total_size'])
                if tfinished_time<=timestamp:
                    if tfinished_time < tfinished_early:
                        tfinished_early = tfinished_time
                        i_early = [i]
                    elif tfinished_time == tfinished_early:
                        i_early.append(i)
                i = i + 1
            #remove the first upload
            i_early.sort(reverse=True)
            if len(i_early)>0:
                for i in i_early:
                    s = self.topologyGraph.node[seekerID]['upload_sessions'][i]
                    if s['HIT'] is True:
                        self.results.add_Hit(s['reqID'],s['URL'],s['total_size'],tfinished_early-s['start_timestamp']+self.request_pserver_time)
                        self.register_in_local_host(s['clientID'],s['URL'],s['total_size'],tfinished_early)                        
                    else:
                        if self.results.add_miss(s['reqID'],s['URL'],s['total_size'],tfinished_early-s['start_timestamp']+self.request_pserver_time,1) is True:
                            self.register_in_local_host(s['clientID'],s['URL'],s['total_size'],tfinished_early+self.request_pserver_time)                            
                    peerID = self.topologyGraph.node[seekerID]['upload_sessions'][i]['clientID']        
                    self.topologyGraph.node[seekerID]['upload_sessions'].pop(i)
                    self.topologyGraph.node[peerID]['upload_pserver_sessions'] = \
                        self.topologyGraph.node[peerID]['upload_pserver_sessions'] - 1
                    
                if len(self.topologyGraph.node[seekerID]['upload_sessions'])>0:                
                    self.topologyGraph.node[seekerID]['available_uploadBW'] = \
                            self.bw_pserver_upload/float(len(self.topologyGraph.node[seekerID]['upload_sessions']))
                else:
                    self.topologyGraph.node[seekerID]['available_uploadBW'] = self.bw_pserver_upload
                #now check each unfinished upload and update BW for them
                sessions = self.topologyGraph.node[seekerID]['upload_sessions']
                            
                for i in range(len(sessions)):
                    s = self.topologyGraph.node[seekerID]['upload_sessions'][i]
                    retreived_size = (tfinished_early-s['last_time'])*s['BW']
                    peerID = self.topologyGraph.node[seekerID]['upload_sessions'][i]['clientID']                    
                    available_peer_bw = self.bw_client_pserver/self.topologyGraph.node[peerID]['upload_pserver_sessions']
                    if self.topologyGraph.node[seekerID]['available_uploadBW']<available_peer_bw:
                        self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = self.topologyGraph.node[seekerID]['available_uploadBW']
                    else:
                        self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = available_peer_bw
                    self.topologyGraph.node[seekerID]['upload_sessions'][i]['last_time']=tfinished_early
                    self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']=retreived_size + \
                                self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']
                    if self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']>self.topologyGraph.node[seekerID]['upload_sessions'][i]['total_size']:
                        self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size'] = self.topologyGraph.node[seekerID]['upload_sessions'][i]['total_size']
                        #print 'high retrieved size local'
                    
            else: #if i_early<0 it means there are not any finished upload until timestamp 
                break
            #endwhile   
        #calculate retrievedSize of any unfinished upload until timestamp
        sessions = self.topologyGraph.node[seekerID]['upload_sessions']
        for i in range(len(sessions)):
            s = self.topologyGraph.node[seekerID]['upload_sessions'][i]
            retreived_size = (timestamp-s['last_time'])*s['BW']
            peerID = self.topologyGraph.node[seekerID]['upload_sessions'][i]['clientID']                    
            available_peer_bw = self.bw_client_pserver/self.topologyGraph.node[peerID]['upload_pserver_sessions']
            if self.topologyGraph.node[seekerID]['available_uploadBW']<available_peer_bw:
                self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = self.topologyGraph.node[seekerID]['available_uploadBW']
            else:
                self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = available_peer_bw
            self.topologyGraph.node[seekerID]['upload_sessions'][i]['last_time']=timestamp
            self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']
            if self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size']>self.topologyGraph.node[seekerID]['upload_sessions'][i]['total_size']:
                self.topologyGraph.node[seekerID]['upload_sessions'][i]['retreived_size'] = self.topologyGraph.node[seekerID]['upload_sessions'][i]['total_size']
            
    
    def checkPserver_DLSessions(self, timestamp,seekerID):
       # if len(self.topologyGraph.node[seekerID]['download_sessions'])>5:
#            print len(self.topologyGraph.node[seekerID]['download_sessions'])
        #    print ('shared BW for pserver download='+str(self.topologyGraph.node[seekerID]['download_sessions'][0]['BW']),file=self.f)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            #print 'seekerID'
            #print seekerID
            while i <len(self.topologyGraph.node[seekerID]['download_sessions']):
                
                s = self.topologyGraph.node[seekerID]['download_sessions'][i]
                #print s['URL']
                #computing estimated time for finishing the download with last BW value            
                #t = len/bw + (len/c+1)*d
                #print 'BW in pserver download= ' + str(s['BW'])
                remainedSize = s['total_size']-s['retreived_size']
                t = remainedSize/float(s['BW'])+s['delay']
                tfinished_time = t+s['last_time']
                if tfinished_time<=timestamp:
                    if tfinished_time < tfinished_early:
                        tfinished_early = tfinished_time
                        i_early = [i]
                    elif tfinished_time == tfinished_early:
                        i_early.append(i)
                i = i + 1
            #remove the first upload
            i_early.sort(reverse=True)
            if len(i_early)>0:
                for i in i_early:
                    s = self.topologyGraph.node[seekerID]['download_sessions'][i]
                    if self.results.add_miss(s['reqID'],s['URL'],s['total_size'],tfinished_early-s['start_timestamp']+self.delay_client_pserver,0) is True:
                        self.register_in_local_host(s['clientID'],s['URL'],s['total_size'],tfinished_early+self.delay_client_pserver)                        
                    self.register_in_pserver(seekerID, s['URL'], s['total_size'],tfinished_early)
                    self.topologyGraph.node[seekerID]['download_sessions'].pop(i)
                    
                    
                if len(self.topologyGraph.node[seekerID]['download_sessions'])>0:                
                    self.topologyGraph.node[seekerID]['available_downloadBW'] = \
                            self.bw_pserver_download/float(len(self.topologyGraph.node[seekerID]['download_sessions']))
                else:
                    self.topologyGraph.node[seekerID]['available_downloadBW'] = self.bw_pserver_download
                #now check each unfinished upload and update BW for them
                sessions = self.topologyGraph.node[seekerID]['download_sessions']
                            
                for i in range(len(sessions)):
                    s = self.topologyGraph.node[seekerID]['download_sessions'][i]
                    retreived_size = (tfinished_early-s['last_time'])*s['BW']
                    self.topologyGraph.node[seekerID]['download_sessions'][i]['BW'] = self.topologyGraph.node[seekerID]['available_downloadBW']
                    self.topologyGraph.node[seekerID]['download_sessions'][i]['last_time']=tfinished_early
                    self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']=retreived_size + \
                                self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']
                    if self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']>self.topologyGraph.node[seekerID]['download_sessions'][i]['total_size']:
                        self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size'] = self.topologyGraph.node[seekerID]['download_sessions'][i]['total_size']
                        #print 'high retrieved size local'
                    
            else: #if i_early<0 it means there are not any finished upload until timestamp 
                break
            #endwhile   
        #calculate retrievedSize of any unfinished upload until timestamp
        sessions = self.topologyGraph.node[seekerID]['download_sessions']
        for i in range(len(sessions)):
            s = self.topologyGraph.node[seekerID]['download_sessions'][i]
            retreived_size = (timestamp-s['last_time'])*s['BW']
            self.topologyGraph.node[seekerID]['download_sessions'][i]['BW'] = self.topologyGraph.node[seekerID]['available_downloadBW']
            self.topologyGraph.node[seekerID]['download_sessions'][i]['last_time']=timestamp
            self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']
            if self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size']>self.topologyGraph.node[seekerID]['download_sessions'][i]['total_size']:
                self.topologyGraph.node[seekerID]['download_sessions'][i]['retreived_size'] = self.topologyGraph.node[seekerID]['download_sessions'][i]['total_size']
      
    def addPserver_uploadSession(self, req, lastTimestamp, seekerID,clientID, Hit):
        available_BW_pserver = self.bw_pserver_upload/float(len(self.topologyGraph.node[seekerID]['upload_sessions'])+1)
        available_BW_peer = self.bw_client_pserver/float(self.topologyGraph.node[clientID]['upload_pserver_sessions']+1)
        self.topologyGraph.node[seekerID]['available_uploadBW'] = available_BW_pserver
        if available_BW_peer<available_BW_pserver:
            available_BW = available_BW_peer
        else:
            available_BW = available_BW_pserver
        newsession = {'reqID':req.reqID, 'URL':req.URL, 'total_size':req.responseLen,'retreived_size':0,'start_timestamp':req.timestamp,\
                        'last_time':lastTimestamp,'BW':available_BW,'delay':self.delay_client_pserver,'clientID':clientID,'HIT':Hit}
        self.topologyGraph.node[seekerID]['upload_sessions'].append(newsession)
        self.topologyGraph.node[clientID]['upload_pserver_sessions'] = self.topologyGraph.node[clientID]['upload_pserver_sessions'] +1
        
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[seekerID]['upload_sessions'])):
            client = self.topologyGraph.node[seekerID]['upload_sessions'][i]['clientID']
            available_BW_peer = self.bw_client_pserver/float(self.topologyGraph.node[client]['upload_pserver_sessions'])
            if available_BW_peer<available_BW_pserver:
                self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = available_BW_peer
            else:
                self.topologyGraph.node[seekerID]['upload_sessions'][i]['BW'] = available_BW_pserver
        return available_BW
        
    def addPserver_DLSession(self,req, lastTimestamp, seekerID,clientID,delay):
        available_BW = self.bw_pserver_download/float(len(self.topologyGraph.node[seekerID]['download_sessions'])+1)
        self.topologyGraph.node[seekerID]['available_downloadBW'] = available_BW;
        newsession = {'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,\
                          'BW':available_BW,'delay':delay,'clientID':clientID}
        self.topologyGraph.node[seekerID]['download_sessions'].append(newsession)
        
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[seekerID]['download_sessions'])):
            self.topologyGraph.node[seekerID]['download_sessions'][i]['BW'] = available_BW
        return available_BW
        
    def getFreeCacheSize_localHost(self,clientID, timestamp):
        size = 0
        for cache in self.topologyGraph.node[clientID]['cdn_cache']:
            if cache[2]<=timestamp:
                size = size + cache[1]
        return self.host_MaxCacheSize-size   
        
    def register_in_local_host(self, clientID, url, dataLen,timestamp):
        #check if cache is not full
        freecache=self.getFreeCacheSize(clientID,timestamp)
        if freecache>=dataLen:
            #add to client cache=====
            self.topologyGraph.node[clientID]['cdn_cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cdn_cacheSize']
            self.topologyGraph.node[clientID]['cdn_cache'].insert(0,[url,dataLen,timestamp])
           
        else:
            #replace the content with a LR contents in cache
            #print('local cache: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #print('local cache in CDN: cache size: ' + str(self.topologyGraph.node[clientID]['cdn_cacheSize']),file=self.f)
            while freecache<dataLen and len(self.topologyGraph.node[clientID]['cache'])>0:
                cacheElement = self.topologyGraph.node[clientID]['cache'].pop()
                #print 'free cache: ' + str(freecache)
                self.topologyGraph.node[clientID]['cdn_cacheSize'] = self.topologyGraph.node[clientID]['cdn_cacheSize']-cacheElement[1]
                freecache = freecache + cacheElement[1]
            if freecache>=dataLen:
                self.topologyGraph.node[clientID]['cdn_cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cdn_cacheSize']
                self.topologyGraph.node[clientID]['cdn_cache'].insert(0,[url,dataLen,timestamp])
            
    def getFreeCacheSize_pserver(self,pserverID, timestamp):
        size = 0
        for cache in self.topologyGraph.node[pserverID]['cache']:
            if cache[2]<=timestamp:
                size = size + cache[1]
        return self.pserver_MaxCacheSize   
        
    def register_in_pserver(self, seekerID, url, dataLen,timestamp):
        #check if cache is not full
        freecache=self.getFreeCacheSize_pserver(seekerID,timestamp)
        #print ('cached size in cache server= '+ str(self.topologyGraph.node[seekerID]['cacheSize']) ,file=self.f)
        if freecache>=dataLen:
            #add to client cache=====
            self.topologyGraph.node[seekerID]['cacheSize'] = dataLen + self.topologyGraph.node[seekerID]['cacheSize']
            self.topologyGraph.node[seekerID]['cache'].insert(0,[url,dataLen,timestamp])
           
        else:
            #replace the content with a LR contents in cache
            print ('pserver: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #print('pserver: cache size: ' + str(self.topologyGraph.node[seekerID]['cacheSize']),file=self.f)
            while freecache<dataLen and len(self.topologyGraph.node[seekerID]['cache'])>0:
                cacheElement = self.topologyGraph.node[seekerID]['cache'].pop()
                #print 'free cache: ' + str(freecache)
                self.topologyGraph.node[seekerID]['cacheSize'] = self.topologyGraph.node[seekerID]['cacheSize']-cacheElement[1]
                freecache = freecache + cacheElement[1]
            if freecache>=dataLen:
                self.topologyGraph.node[seekerID]['cacheSize'] = dataLen + self.topologyGraph.node[seekerID]['cacheSize']
                self.topologyGraph.node[seekerID]['cache'].insert(0,[url,dataLen,timestamp])
        
    def compuet_CDN_time(self, req, ex_pserver_bw, ex_pserver_delay):
        if (req.reqID==331):
            print ('*')
        clientID = self.clientIDs[req.clientIP]
        #print 'clientID'           
        #print clientID
        seekerID = self.topologyGraph.node[clientID]['seeker']
        if self.check_in_localCache_CDN(req,clientID):
            self.results.add_localDL_CDN(req.reqID,req.URL,req.responseLen)
            self.local_foundnum_CDN = self.local_foundnum_CDN + 1
            return [clientID, 0]
        #print seekerID
        for cacheIndx in range(len(self.topologyGraph.node[seekerID]['cache'])):
            if self.topologyGraph.node[seekerID]['cache'][cacheIndx][0]==req.URL and \
            self.topologyGraph.node[seekerID]['cache'][cacheIndx][2]<=req.timestamp:
                cacheElement = self.topologyGraph.node[seekerID]['cache'].pop(cacheIndx)
                self.topologyGraph.node[seekerID]['cache'].insert(0,cacheElement)
                self.checkPserver_uploadSessions(req.timestamp,seekerID)
                self.addPserver_uploadSession(req, req.timestamp , seekerID,clientID,True)
                self.CDN_Hit = self.CDN_Hit + 1
                return
                
#        self.checkPserver_DLSessions(req.timestamp,seekerID)
        estimatedResponseTime = req.responseLen/ex_pserver_bw + ex_pserver_delay
        self.register_in_pserver(seekerID,req.URL,req.responseLen,req.timestamp+estimatedResponseTime)
        if self.results.add_miss(req.reqID,req.URL,req.responseLen,estimatedResponseTime+self.delay_client_pserver+self.request_pserver_time,0) is True:
            self.register_in_local_host(clientID,req.URL,req.responseLen,req.timestamp+estimatedResponseTime+self.delay_client_pserver+self.request_pserver_time)
        
        self.checkPserver_uploadSessions(req.timestamp,seekerID)
        self.addPserver_uploadSession(req,req.timestamp,seekerID,clientID,False)
        
#        self.addPserver_DLSession(req, req.timestamp, seekerID,clientID,ex_pserver_delay)
#        self.CDN_miss = self.CDN_miss + 1
                
                
        
   #dictonariy:[{receiver_peer, isLocalPeer, URL, total_size,retreived_size,start_timestamp,last_time,BW}]
    #total_size: total size of content
    #retreived_size: the amount of content that is retrieved untill now
    #last_time: timestamp of last BW change
    #BW: current upload BW of corresponding cache
    #every time that a new upload is started from the corresponding cache, BW is changed and the amount of data that is 
    #retrived untill now is computed, if finish remove from the sessions
    #if download is finished add the content to local cache
    #return available upload BW for correspondig link
    def checkLocalSessions_s1(self, timestamp, peerID):
        #at first remove each finished upload and update the BW
        #sessions = self.topologyGraph.node[peerID]['upload_sessions']
        if len(self.topologyGraph.node[peerID]['upload_sessions_s1'])>1:
#            print len(self.topologyGraph.node[peerID]['upload_sessions'])
            print ('shared BW for local p2p s1='+str(self.topologyGraph.node[peerID]['upload_sessions_s1'][0]['BW']),file=self.f)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            while i <len(self.topologyGraph.node[peerID]['upload_sessions_s1']):
                
                s = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]
                #print s['URL']
                #computing estimated time for finishing the download with last BW value            
                #t = len/bw + (len/c+1)*d
                remainedSize = s['total_size']-s['retreived_size']
                t = remainedSize/float(s['BW'])+self.delay_p2p_layer1 #(s['total_size']/self.tcp_size+1)*self.delay_p2p_layer1
                #print 'total size= '+str(s['total_size'])        
                #print 'remainedSize= '+str(remainedSize)
                #print 'BW in local p2p= ' + str(s['BW'])                
                #print 'speed= '+ str(s['total_size']/float(t))
                #print '------------------------------------------'
                tfinished_time = t+s['last_time']
                if tfinished_time<=timestamp:
                    if tfinished_time < tfinished_early:
                        tfinished_early = tfinished_time
                        i_early = [i]
                    elif tfinished_time == tfinished_early:
                        i_early.append(i)
                i = i + 1
            #remove the first upload
            i_early.sort(reverse=True)
            if len(i_early)>0:
                for i in i_early:
                    s = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],tfinished_early)
                    self.topologyGraph.node[peerID]['upload_sessions_s1'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if rtime>s['hhead_overhead']:
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],True)
                    else:
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,True)
                if len(self.topologyGraph.node[peerID]['upload_sessions_s1'])>0:                
                    self.topologyGraph.node[peerID]['available_uploadBW_s1'] = \
                            self.bw_p2p_upload_layer1/float(len(self.topologyGraph.node[peerID]['upload_sessions_s1']))
                else:
                    self.topologyGraph.node[peerID]['available_uploadBW_s1'] = self.bw_p2p_upload_layer1
                #now check each unfinished upload and update BW for them
                sessions = self.topologyGraph.node[peerID]['upload_sessions_s1']
                            
                for i in range(len(sessions)):
                    s = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]
                    retreived_size = (tfinished_early-s['last_time'])*s['BW']
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['BW'] = self.topologyGraph.node[peerID]['available_uploadBW_s1']
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['last_time']=tfinished_early
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']=retreived_size + \
                                self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']
                    if self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']:
                        self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']
                        #print 'high retrieved size local'
                    
            else: #if i_early<0 it means there are not any finished upload until timestamp 
                break
        #endwhile   
        #calculate retrievedSize of any unfinished upload until timestamp
        sessions = self.topologyGraph.node[peerID]['upload_sessions_s1']
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]
            retreived_size = (timestamp-s['last_time'])*s['BW']
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['BW'] = self.topologyGraph.node[peerID]['available_uploadBW_s1']
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['last_time']=timestamp
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']
            if self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']:
                self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']
                
    
    def checkLocalSessions_s2(self, timestamp, peerID):
        #at first remove each finished upload and update the BW
        #sessions = self.topologyGraph.node[peerID]['upload_sessions']
        if len(self.topologyGraph.node[peerID]['upload_sessions_s2'])>1:
#            print len(self.topologyGraph.node[peerID]['upload_sessions'])
            print ('shared BW for local p2p s2='+str(self.topologyGraph.node[peerID]['upload_sessions_s2'][0]['BW']),file=self.f)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            while i <len(self.topologyGraph.node[peerID]['upload_sessions_s2']):
                
                s = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]
                #print s['URL']
                #computing estimated time for finishing the download with last BW value            
                #t = len/bw + (len/c+1)*d
                remainedSize = s['total_size']-s['retreived_size']
                t = remainedSize/float(s['BW'])+self.delay_p2p_layer2 #(s['total_size']/self.tcp_size+1)*self.delay_p2p_layer2
                #print 'total size= '+str(s['total_size'])        
                #print 'remainedSize= '+str(remainedSize)
                #print 'BW in local p2p= ' + str(s['BW'])                
                #print 'speed= '+ str(s['total_size']/float(t))
                #print '------------------------------------------'
                tfinished_time = t+s['last_time']
                if tfinished_time<=timestamp:
                    if tfinished_time < tfinished_early:
                        tfinished_early = tfinished_time
                        i_early = [i]
                    elif tfinished_time == tfinished_early:
                        i_early.append(i)
                i = i + 1
            #remove the first upload
            i_early.sort(reverse=True)
            if len(i_early)>0:
                for i in i_early:
                    s = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],tfinished_early)
                    self.topologyGraph.node[peerID]['upload_sessions_s2'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if rtime>s['hhead_overhead']:
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],True)
                    else:
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,True)
                if len(self.topologyGraph.node[peerID]['upload_sessions_s2'])>0:                
                    self.topologyGraph.node[peerID]['available_uploadBW_s2'] = \
                            self.bw_p2p_upload_layer2/float(len(self.topologyGraph.node[peerID]['upload_sessions_s2']))
                else:
                    self.topologyGraph.node[peerID]['available_uploadBW_s2'] = self.bw_p2p_upload_layer2
                #now check each unfinished upload and update BW for them
                sessions = self.topologyGraph.node[peerID]['upload_sessions_s2']
                            
                for i in range(len(sessions)):
                    s = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]
                    retreived_size = (tfinished_early-s['last_time'])*s['BW']
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['BW'] = self.topologyGraph.node[peerID]['available_uploadBW_s2']
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['last_time']=tfinished_early
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']=retreived_size + \
                                self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']
                    if self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']:
                        self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']
                        #print 'high retrieved size local'
                    
            else: #if i_early<0 it means there are not any finished upload until timestamp 
                break
        #endwhile   
        #calculate retrievedSize of any unfinished upload until timestamp
        sessions = self.topologyGraph.node[peerID]['upload_sessions_s2']
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]
            retreived_size = (timestamp-s['last_time'])*s['BW']
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['BW'] = self.topologyGraph.node[peerID]['available_uploadBW_s2']
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['last_time']=timestamp
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']
            if self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']:
                self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']              
                  
    def checkRemoteSessions(self, timestamp, peerID):
        #at first remove each finished upload and update the BW
        #sessions = self.topologyGraph.node[peerID]['upload_sessions']
        #if len(self.topologyGraph.node[peerID]['upload_remote_sessions'])>5:
        #    print len(self.topologyGraph.node[peerID]['upload_remote_sessions'])
            #print ('shared BW for remote p2p='+str(self.topologyGraph.node[peerID]['upload_remote_sessions'][0]['BW']),file=self.f)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            while i <len(self.topologyGraph.node[peerID]['upload_remote_sessions']):
                
                s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
                #print s['URL']
                #computing estimated time for finishing the download with last BW value            
                #t = len/bw + (len/c+1)*d
                remainedSize = s['total_size']-s['retreived_size']
                t = remainedSize/float(s['BW'])+self.delay_p2p_remote#(s['total_size']/self.tcp_size+1)*self.delay_p2p_remote
                tfinished_time = t+s['last_time']
                #print 'BW in remote p2p= ' + str() 
                if tfinished_time<=timestamp:
                    if tfinished_time < tfinished_early:
                        tfinished_early = tfinished_time
                        i_early = [i]
                    elif tfinished_time == tfinished_early:
                        i_early.append(i)
                i = i + 1
            #remove the first upload
            i_early.sort(reverse=True)
            if len(i_early)>0:
                for i in i_early:
                    s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],t+s['last_time'])
                    self.topologyGraph.node[peerID]['upload_remote_sessions'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if rtime>s['hhead_overhead']:                    
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],False)
                    else:
                        self.results.add_peerDL(s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,False)
                    
                if len(self.topologyGraph.node[peerID]['upload_remote_sessions'])>0:                
                    self.topologyGraph.node[peerID]['available_remote_uploadBW'] = \
                            self.bw_p2p_remote_upload/float(len(self.topologyGraph.node[peerID]['upload_remote_sessions']))
                else:
                    self.topologyGraph.node[peerID]['available_remote_uploadBW'] = self.bw_p2p_remote_upload
                #now check each unfinished upload and update BW for them
                sessions = self.topologyGraph.node[peerID]['upload_remote_sessions']
                for i in range(len(sessions)):
                    s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
                    retreived_size = (tfinished_early-s['last_time'])*s['BW']
                    self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['BW'] = self.topologyGraph.node[peerID]['available_remote_uploadBW']
                    self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['last_time']=tfinished_early
                    self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']=retreived_size + \
                                self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']
                    if self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['total_size']:
                        self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['total_size']
            else: #if i_early<0 it means there are not any finished upload until timestamp 
                break
        #endwhile 
        #calculate retrievedSize of any unfinished upload until timestamp        
        sessions = self.topologyGraph.node[peerID]['upload_remote_sessions']
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
            retreived_size = (timestamp-s['last_time'])*s['BW']
            self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['BW'] = self.topologyGraph.node[peerID]['available_remote_uploadBW']
            self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['last_time']=timestamp
            self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']=retreived_size + \
                self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']
            if self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['total_size']:
                self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['total_size']
            
    #check if a client with a given IP is alive at time t_now or not
    #
    def is_alive(self,ip,t_now):
        if random.random()<self.aliveProb:
            return True
        return False
#        T = t_now-self.arrivalTimes[ip]
#        a = T / (4*60*60*1000000)           #every 2 hour the status of the client is changed
#        if a/2==0:
#            return True
#        else:
#            return False
#        return True
    #this function is for corresponding an IP to a client of the topology    
    def setClientsIP(self,iplist):
        iplist.sort()
        for seeker in self.seeker_nodes:
            for switch in self.topologyGraph.neighbors(seeker):
                if self.topologyGraph.node[switch]['tier']=='edge':
                    for host in self.topologyGraph.neighbors(switch):
                        if self.topologyGraph.node[host]['type']=='host' and len(iplist)>0:
                            self.topologyGraph.node[host]['ip'] = iplist.pop(0)
                            self.clientIDs[self.topologyGraph.node[host]['ip']] = host
                            self.topologyGraph.node[host]['seeker'] = seeker
                            self.topologyGraph.node[host]['switch'] = switch
                        
        #print (self.clientIDs)
                    
                    
    #{receiver_peer, isLocalPeer, URL, total_size,retreived_size,start_timestamp,last_time,BW}
    def addRemoteSession(self, req, lastTimestamp, providerPeer, overhead,hhead_overhead):
        available_BW = self.bw_p2p_remote_upload/float(len(self.topologyGraph.node[providerPeer]['upload_remote_sessions'])+1)
        self.topologyGraph.node[providerPeer]['available_remote_uploadBW'] = available_BW;
        newsession = {'receiver_peer':req.clientIP,'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':available_BW,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_remote_sessions'].append(newsession)
        
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_remote_sessions'])):
            self.topologyGraph.node[providerPeer]['upload_remote_sessions'][i]['BW'] = available_BW
            
    def addLocalSession_s1(self, req, lastTimestamp, providerPeer, overhead, hhead_overhead):
        available_BW = self.bw_p2p_upload_layer1/float(len(self.topologyGraph.node[providerPeer]['upload_sessions_s1'])+1)
        self.topologyGraph.node[providerPeer]['available_uploadBW_s1'] = available_BW;
        newsession = {'receiver_peer':req.clientIP, 'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':available_BW,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_sessions_s1'].append(newsession)
        
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_sessions_s1'])):
            self.topologyGraph.node[providerPeer]['upload_sessions_s1'][i]['BW'] = available_BW
    
    def addLocalSession_s2(self, req, lastTimestamp, providerPeer, overhead, hhead_overhead):
        available_BW = self.bw_p2p_upload_layer2/float(len(self.topologyGraph.node[providerPeer]['upload_sessions_s2'])+1)
        self.topologyGraph.node[providerPeer]['available_uploadBW_s2'] = available_BW;
        newsession = {'receiver_peer':req.clientIP, 'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':available_BW,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_sessions_s2'].append(newsession)
        
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_sessions_s2'])):
            self.topologyGraph.node[providerPeer]['upload_sessions_s2'][i]['BW'] = available_BW
       
    
    def check_in_localCache_CDN(self,req,clientID):
        for i in range(len(self.topologyGraph.node[clientID]['cdn_cache'])):
            if self.topologyGraph.node[clientID]['cdn_cache'][i][0]==req.URL and \
                self.topologyGraph.node[clientID]['cdn_cache'][i][2]<=req.timestamp:
                return True
        return False         
     
    def check_in_localCache(self,req,clientID):
        for i in range(len(self.topologyGraph.node[clientID]['cache'])):
            if self.topologyGraph.node[clientID]['cache'][i][0]==req.URL and \
                self.topologyGraph.node[clientID]['cache'][i][2]<=req.timestamp:
                return True
        return False
                                             
    #this function seek a content in other peers
    #return [peerID,responseTime or seek time],
    #if a peer is found it return peerID and responseTime+seektime to get data from this peer
    #if no peer is found only seek time is returned with peerID=-1                
    def seek(self,req, bw_delay, web_responseTime):
        clientID = self.clientIDs[req.clientIP]     
        if self.check_in_localCache(req,clientID):
            self.results.add_localDL(req.reqID,req.URL,req.responseLen)
            self.local_foundnum = self.local_foundnum + 1
            #print ('find in local cache')
            return [clientID, 0]
            
        seekerID = self.topologyGraph.node[clientID]['seeker']
        http_head_overhead = (self.httpHEAD_req_len+self.httpHEAD_response_len)/bw_delay[0]+2*bw_delay[1]            
        #http_head_overhead = 0
        if self.topologyGraph.node[seekerID]['lookupTable'][req.URL]!=None:       
            #select the peer from available cache which its corresponding upload BW is larger
            max_bw=0
            selected_peer=-1
            for cache in self.topologyGraph.node[seekerID]['lookupTable'][req.URL]:
                #print ('find in cache, cache[\'timestamp\']:'+str(cache['timestamp'])+ ',req.timestamp:'+ str(req.timestamp ))
                if cache['timestamp']<=req.timestamp and self.is_alive(cache['clientIP'],req.timestamp):
                    if self.topologyGraph.node[cache['clientID']]['switch']==self.topologyGraph.node[clientID]['switch']:                    
                        if self.topologyGraph.node[cache['clientID']]['available_uploadBW_s1']>max_bw:
                            max_bw = self.topologyGraph.node[cache['clientID']]['available_uploadBW_s1']
                            selected_peer = cache['clientID']
                    else:
                        if self.topologyGraph.node[cache['clientID']]['available_uploadBW_s2']>max_bw:
                            max_bw = self.topologyGraph.node[cache['clientID']]['available_uploadBW_s2']
                            selected_peer = cache['clientID']
                    #print ('find in cache')
            if(max_bw>0):
                #move this cache to the beginning of the cache list in order to implementing LRU for cache replacement
                for cacheIndx in range(len(self.topologyGraph.node[selected_peer]['cache'])):
                    if self.topologyGraph.node[selected_peer]['cache'][cacheIndx][0]==req.URL:
                        cacheElement = self.topologyGraph.node[selected_peer]['cache'].pop(cacheIndx)
                        self.topologyGraph.node[selected_peer]['cache'].insert(0,cacheElement)
                        break
                        
                
                overhead = self.seek_client_seeker_time+self.seekResponse_client_seeker_time# + http_head_overhead
                            
                #for peer in self.host_nodes:
                self.checkLocalSessions_s2(req.timestamp+overhead,selected_peer)
                self.checkLocalSessions_s1(req.timestamp+overhead,selected_peer)
                self.checkRemoteSessions(req.timestamp+overhead,selected_peer)
                if self.topologyGraph.node[selected_peer]['switch']==self.topologyGraph.node[clientID]['switch']:
                    self.addLocalSession_s1(req, req.timestamp + overhead, selected_peer,overhead,http_head_overhead)
                else:
                    self.addLocalSession_s2(req, req.timestamp + overhead, selected_peer,overhead,http_head_overhead)                    
                self.localPeer_foundnum = self.localPeer_foundnum + 1
                #print ('find in local peers')
                return [selected_peer, overhead]
            
        neighbor_seekers = [nseeker for nseeker in self.topologyGraph.neighbors(seekerID) if self.topologyGraph.node[nseeker]['tier']=='core']
        

        #select the peer from available remote cache which its corresponding upload BW is larger
        lookedSeekers = 0        
        max_bw=0
        selected_peer=-1
        for nseeker in neighbor_seekers: 
            lookedSeekers = lookedSeekers + 1;
            if self.topologyGraph.node[nseeker]['lookupTable'][req.URL]!=None:        
                for cache in self.topologyGraph.node[nseeker]['lookupTable'][req.URL]:
                    if cache['timestamp']<=req.timestamp and self.is_alive(cache['clientIP'],req.timestamp)\
                        and self.topologyGraph.node[cache['clientID']]['available_remote_uploadBW']>max_bw:
                        max_bw = self.topologyGraph.node[cache['clientID']]['available_remote_uploadBW']
                        selected_peer = cache['clientID']
        
        overhead = self.seek_client_seeker_time+self.seekResponse_client_seeker_time +\
                        (self.seek_seeker_seeker_time+self.seekResponse_seeker_seeker_time)# + http_head_overhead
        if(max_bw>0): #if found and estimated time is less than web response time
            #move this cache to the beginning of the cache list in order to implementing LRU for cache replacement
            #estimated_responseTime = overhead+req.responseLen/(float(max_bw))+self.delay_p2p_remote
            #if estimated_responseTime<=web_responseTime:
            for cacheIndx in range(len(self.topologyGraph.node[selected_peer]['cache'])):
                if self.topologyGraph.node[selected_peer]['cache'][cacheIndx][0]==req.URL:
                    cacheElement = self.topologyGraph.node[selected_peer]['cache'].pop(cacheIndx)
                    self.topologyGraph.node[selected_peer]['cache'].insert(0,cacheElement)
                    break
                #for peer in self.host_nodes:
                #print ('find in remote peers')
            self.checkLocalSessions_s2(req.timestamp+overhead,selected_peer)
            self.checkLocalSessions_s1(req.timestamp+overhead,selected_peer)
            self.checkRemoteSessions(req.timestamp+overhead,selected_peer)
            self.addRemoteSession(req, req.timestamp+overhead,selected_peer, overhead,http_head_overhead)
            self.remotePeer_foundnum = self.remotePeer_foundnum + 1
            return [selected_peer,overhead]
            #else:
                #print 'retrive from remote peer is not accepted'
                #self.deniedPeerDL = self.deniedPeerDL + 1
        self.notFoundnum = self.notFoundnum + 1
        self.results.add_webDL(req.reqID,req.URL,req.responseLen,web_responseTime+overhead,overhead)
        self.register(req.clientIP, req.URL, req.responseLen, req.timestamp+web_responseTime+overhead)
        return [-1,overhead]

    def getFreeCacheSize(self,clientID, timestamp):
        size = 0
        for cache in self.topologyGraph.node[clientID]['cache']:
            if cache[2]<=timestamp:
                size = size + cache[1]
        return self.host_MaxCacheSize-size          
        
   #register a content in cache
    def register_fullRedundant(self,clientIP, URL, dataLen,timestamp):
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']            
        #if len(self.topologyGraph.node[seekerID]['lookupTable'][URL])>0:
        #    return	 
        #clientID = [node for node in self.host_nodes if self.topologyGraph.node[node]['ip']==clientIP][0]
        #print ('register url: '+ URL)
        #register in seeker

        
        #check if cache is not full
        freecache=self.getFreeCacheSize(clientID,timestamp)
        
        if freecache>=dataLen:
            #print ('register url: '+ URL)
            #add to client cache=====
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
            self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
           
        elif dataLen<self.host_MaxCacheSize:
            #replace the content with a LR contents in cache
            print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #print('peer: cache size: ' + str(self.topologyGraph.node[clientID]['cacheSize']),file=self.f)
            while freecache<dataLen and len(self.topologyGraph.node[clientID]['cache'])>0 :
                cacheElement = self.topologyGraph.node[clientID]['cache'].pop()
                #print 'free cache: ' + str(freecache)
                self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                removed_URL = cacheElement[0]                
                #remove from seeker too
                i = 0
                while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                    if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                        self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                        break
                    i = i + 1
                        
                freecache = freecache + cacheElement[1]
            if(freecache>=dataLen):
                self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
                self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
                self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
                
    #register a content in cache
    def register_noRedundant(self,clientIP, URL, dataLen,timestamp):
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']            
        if self.topologyGraph.node[seekerID]['lookupTable'][URL]!=None:
            if len(self.topologyGraph.node[seekerID]['lookupTable'][URL])>0:
                if self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['timestamp']>timestamp:
                    self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['timestamp'] = timestamp
                    removedID = self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['clientID']
                    self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['clientID'] = clientID
                    for cacheIndx in range(len(self.topologyGraph.node[removedID]['cache'])):
                        if self.topologyGraph.node[removedID]['cache'][cacheIndx][0]==URL:
                            self.topologyGraph.node[removedID]['cache'].pop(cacheIndx)
                            break
                    return
                else:
                    return	 
                    
        #clientID = [node for node in self.host_nodes if self.topologyGraph.node[node]['ip']==clientIP][0]
        #print ('register url: '+ URL)
        #register in seeker

        
        #check if cache is not full
        freecache=self.getFreeCacheSize(clientID,timestamp)
        
        if freecache>=dataLen:
            #print ('register url: '+ URL)
            #add to client cache=====
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
            self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
           
        elif dataLen<self.host_MaxCacheSize:
            #replace the content with a LR contents in cache
            print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #search in other peers to find a free cache storage
            for peer in self.topologyGraph.neighbors(seekerID):
                if self.topologyGraph.node[peer]['tier']=='leaf':
                    if self.getFreeCacheSize(peer,timestamp)>dataLen:
                        print('upload cache to another peer',file=self.f)
                        req = Request(-1, self.topologyGraph.node[peer]['ip'], URL, timestamp, dataLen)
                        if self.topologyGraph.node[peer]['switch']==self.topologyGraph.node[clientID]['switch']:
                            self.checkLocalSessions_s1(timestamp,clientID)
                            self.addLocalSession_s1(req, timestamp, clientID,-1,-1)
                        else:
                            self.checkLocalSessions_s1(timestamp,clientID)
                            self.addLocalSession_s2(req, timestamp, clientID,-1,-1)
                    return
            
            #print('peer: cache size: ' + str(self.topologyGraph.node[clientID]['cacheSize']),file=self.f)
            print('peer: cache replacement',file=self.f)
            while freecache<dataLen and len(self.topologyGraph.node[clientID]['cache'])>0 :
                cacheElement = self.topologyGraph.node[clientID]['cache'].pop()
                #print 'free cache: ' + str(freecache)
                self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                removed_URL = cacheElement[0]                
                #remove from seeker too
                i = 0
                while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                    if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                        self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                        break
                    i = i + 1
                        
                freecache = freecache + cacheElement[1]
            if(freecache>=dataLen):
                self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
                self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
                self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
                
                
    def register_popularityBased(self,clientIP, URL, dataLen,timestamp):
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']       
        available_redundancy = len(self.topologyGraph.node[seekerID]['lookupTable'][URL])-1
        if available_redundancy>=0:
            first_time = self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['timestamp']
            req_num = self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['req_num']
            if (timestamp-first_time)<=0:
                r = req_num/float(1)
            else:
                r = req_num/float(timestamp-first_time)
            cache_redundancy = r*self.max_redundancy
            print ("cache redundancy: "+str(cache_redundancy),file=self.f)
            if cache_redundancy<=available_redundancy:
                return	 
        else:
            self.topologyGraph.node[seekerID]['lookupTable'][URL].append({'timestamp':timestamp,'req_num':1})
        #clientID = [node for node in self.host_nodes if self.topologyGraph.node[node]['ip']==clientIP][0]
        #print ('register url: '+ URL)
        #register in seeker

        
        #check if cache is not full
        freecache=self.host_MaxCacheSize-self.topologyGraph.node[clientID]['cacheSize']
        
        if freecache>=dataLen:
            
            #add to client cache=====
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
            self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
           
        elif dataLen<self.host_MaxCacheSize:
            
            print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #find a registered host in seeker with minimum cacheSize
            min_size = self.host_MaxCacheSize
            for host in self.host_nodes:
                if self.topologyGraph.node[host]['ip']!="" and self.topologyGraph.node[host]['cacheSize']<=min_size:
                    min_size = self.topologyGraph.node[host]['cacheSize']
                    selected_peer = host
            print ('selected_peer:'+str(selected_peer))
            print ('min_size:'+str(min_size))
            if self.host_MaxCacheSize - min_size>=dataLen:
                self.checkLocalSessions_s2(timestamp,clientID)
                self.checkLocalSessions_s1(timestamp,clientID)
                self.checkRemoteSessions(timestamp,clientID)
                req = Request( -1, self.topologyGraph.node[selected_peer]['ip'], URL, timestamp, dataLen)
                print (self.topologyGraph.node[selected_peer]['switch'])
                print (self.topologyGraph.node[clientID]['switch'])
                if self.topologyGraph.node[selected_peer]['switch']==self.topologyGraph.node[clientID]['switch']:
                    self.addLocalSession_s1(req, timestamp, clientID,-1,-1)
                else:
                    self.addLocalSession_s2(req, timestamp, clientID,-1,-1)   
                return
            #replace the content with a LR contents in cache
            #print('peer: cache size: ' + str(self.topologyGraph.node[clientID]['cacheSize']),file=self.f)
            while freecache<dataLen and len(self.topologyGraph.node[clientID]['cache'])>0 :
                cacheElement = self.topologyGraph.node[clientID]['cache'].pop()
                #print 'free cache: ' + str(freecache)
                self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                removed_URL = cacheElement[0]                
                #remove from seeker too
                i = 1
                while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                    if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                        self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                        break
                    i = i + 1
                        
                freecache = freecache + cacheElement[1]
            if(freecache>=dataLen):
                self.topologyGraph.node[seekerID]['lookupTable'][URL].append({"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
                self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
                self.topologyGraph.node[clientID]['cache'].insert(0,[URL,dataLen,timestamp])
           
if __name__=='__main__':
    t = Topology(4, 2, 20, 3,'1',100)
    nx.draw(t.topologyGraph)
   
    
