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
import os
import copy
import math


class Topology(object):
    #each two seekers are neighbors with the probability of 1/seeker_neighbor_prob
    #n_seekers: number of local networks
    #n_hosts: total number of hosts
    #n_switches: number of switches for each local network
    def __init__(self, dataset, n_seekers,hosts, seeker_neighbor_prob, aliveProb, cache_policy, 
                 cache_size, outputPath):
        self.fpop = open('popularity','w')
        self.dataset = dataset
        if cache_policy=='fully_redundant':
            self.register = self.register_fullRedundant
        elif cache_policy=='no_redundant':
            self.register = self.register_noRedundant
        else:
            self.register = self.register_popularityBased
        if dataset=='Berkeley':
            self.simulate_proxy = self.simulate_berkeley_proxy
        else:
            self.simulate_proxy = self.extract_ircache_proxy
        self.cache_policy = cache_policy
        self.url_reqNum = defaultdict(int)    #number of requests for each url
        self.reqNum = []                      #sorted list of all request numbers
        self.reqNum_index = defaultdict()     #index of reqNum in sorted list
        self.clientIDs = dict()
        #self.arrivalTimes = IPs_timestamp
        self.aliveProb = aliveProb/float(100)
        #self.tcp_size = 64*(10**3)*8#64KB
        self.bw_p2p_upload_layer1 = float(80000/8)#Mbps
        self.bw_p2p_upload_layer2 = float(70000/8)#Mbps
        self.bw_p2p_remote_upload = float(60000/8)#Mbps
        self.bw_client_pserver = float(80000/8)
        self.bw_client_download = float(80000/8)
        self.bw_pserver_upload = float(800000/8)
        self.external_bw = float(800000/8)
#        if (load=='high'):
#            self.bw_p2p_upload_layer1 = float(80000/8)#KB/s
#            self.bw_p2p_upload_layer2 = float(70000/8)#KB/s
#            self.bw_p2p_remote_upload = float(60000/8)#KB/s
#            self.bw_client_pserver = float(50000/8)
#            self.bw_client_download = float(80000/8)
#            self.bw_pserver_upload = float(800000/8)
#            self.external_bw = float(800000/8)
#        else:
#            self.bw_p2p_upload_layer1 = float(80000/8)#Mbps
#            self.bw_p2p_upload_layer2 = float(80000/8)#Mbps
#            self.bw_p2p_remote_upload = float(70000/8)#Mbps
#            self.bw_client_pserver = float(80000/8)
#            self.bw_client_download = float(80000/8)
#            self.bw_pserver_upload = float(800000/8)
#            self.external_bw = float(800000/8)
        
        #seek packet len = headeLen+dataLen=(4*16)+16
        self.bw_client_seeker = float(100000/8)#100Mb/s 
        self.bw_seeker_seeker = float(100000/8)#100Mb/s
         
        self.delay_client_pserver = 0.5#ms
        self.delay_client_seeker = 0.5#ms
 
        self.delay_seeker_seeker = 10#ms
      
        self.delay_p2p_layer1 = 0.25#ms
        self.delay_p2p_layer2 = 0.5#ms
        self.delay_p2p_remote = 10#ms
        
        #seek_msg_len = udp_header_len+msg_len=8Byte+(contentID+msgType)=8*8+1*8=9 Byte
        #seek_found_len = udp_header_len + msg_len = 8Byte+(contentID+msgType+peerID)=8*8+1*8=9 Byte
        #seek_notfound_len = udp_header_len + msg_len = 8Byte+(contentID+msgType)=8*8+1*8=9Byte
        #UDP header size = 52Byte
        self.seek_client_seeker_time = self.delay_client_seeker#+(52*8+9*8)/self.bw_client_seeker
        self.seek_seeker_seeker_time = self.delay_seeker_seeker#+(52*8+9*8)/self.bw_seeker_seeker
        #seek response packet len = headeLen+dataLen=(4*16)+5*8
        self.seekResponse_client_seeker_time = self.delay_client_seeker#+(52*8+9*8)/self.bw_client_seeker
        self.seekResponse_seeker_seeker_time = self.delay_seeker_seeker#+(52*8+9*8)/self.bw_seeker_seeker
        
        self.request_pserver_time = self.delay_client_pserver#+(8000*8)/self.bw_client_pserver
        
#        self.httpHEAD_req_len = 1000 #Bytes
        self.httpHEAD_response_len = (245+300+245*3+1 + 100) #Encrypted_hash+pk+Enc(D,Kp)+1##1024+8000+4096+1 + headLen
        
        
        self.host_MaxCacheSize = cache_size  #B
        self.LRU_Q_LEN = int(math.ceil(math.log(self.host_MaxCacheSize,2)))
                
        self.localPeer_foundnum = 0
        self.remotePeer_foundnum = 0
        self.notFoundnum = 0
        self.local_foundnum = 0
        self.local_foundnum_CDN = 0
        self.deniedPeerDL = 0
        self.CDN_Hit = 0
        self.CDN_miss = 0
       
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)        
        self.f = open(outputPath+'/log.txt','w')
              
        #an object for logging results
        self.results = Results(outputPath)
        self.results.initializeFiles()
        
        n_hosts = 0     #number of hosts in each local network
        if dataset=='IRCache':
            for n in hosts.keys():
                n_hosts = len(hosts[n]) if n_hosts<len(hosts[n]) else n_hosts
        else:
            n_hosts = len(hosts['berkeley'])/n_seekers+1
        print(n_hosts)
        n_switches = n_hosts/24+1
        #n_hosts_for_each_switch = n_hosts/n_switches + 1
        self.topologyGraph = fnss.two_tier_topology(n_seekers, n_switches*n_seekers, 24)
        #remove all the core nodes and its links and add seeker neighbors
        tiers_type = nx.get_node_attributes(self.topologyGraph,'tier')
        #adding lookup table to seekers (tier=core)
        #print (tiers_type)
        self.seeker_nodes = [node for node in tiers_type
                             if tiers_type[node] == 'core']
                                        
        #node['lookupTable']=[('URL1',node1,node2,...),('URL2',node1,node2,...),...]
        self.max_redundancy = defaultdict()
        for node in self.seeker_nodes:
            
            self.topologyGraph.node[node]['lookupTable'] = defaultdict(list)
            self.topologyGraph.node[node]['cache'] = dict()
            self.topologyGraph.node[node]['tm'] = 0
            self.topologyGraph.node[node]['lru'] = dict()
            self.topologyGraph.node[node]['cacheSize'] = 0
            self.topologyGraph.node[node]['ip']=""
            self.topologyGraph.node[node]['available_uploadBW'] = self.bw_client_pserver
            #list of correspondig p2p upload sessions
            self.topologyGraph.node[node]['upload_sessions'] = []            
            self.topologyGraph.node[node]['download_sessions'] = [] 
            self.topologyGraph.node[node]['download_sessions_web'] = []  
            
            
        #adding cache size to hosts and replacement policy (tier=leaf)
        self.host_nodes = [node for node in tiers_type
                           if tiers_type[node] == 'leaf']
                               
        for node in self.host_nodes:
            self.topologyGraph.node[node]['cache'] = dict()
            self.topologyGraph.node[node]['tm'] = 0
            self.topologyGraph.node[node]['lru'] = defaultdict()
            self.topologyGraph.node[node]['cdn_lru'] = defaultdict()
            for i in range(self.LRU_Q_LEN):
                self.topologyGraph.node[node]['lru'][i] = defaultdict()
                self.topologyGraph.node[node]['cdn_lru'][i] = defaultdict()
            self.topologyGraph.node[node]['cacheSize'] = 0            
            self.topologyGraph.node[node]['cdn_cache'] = dict()
            self.topologyGraph.node[node]['cdn_tm'] = 0
            self.topologyGraph.node[node]['cdn_cacheSize'] = 0
            self.topologyGraph.node[node]['ip']=""
            self.topologyGraph.node[node]['available_uploadBW_s1'] = self.bw_p2p_upload_layer1
            self.topologyGraph.node[node]['available_uploadBW_s2'] = self.bw_p2p_upload_layer2
            self.topologyGraph.node[node]['available_remote_uploadBW'] = self.bw_p2p_remote_upload
            #list of correspondig p2p upload sessions
            self.topologyGraph.node[node]['upload_sessions_s1'] = []            
            self.topologyGraph.node[node]['upload_sessions_s2'] = []   
            self.topologyGraph.node[node]['download_sessions'] = []   
            self.topologyGraph.node[node]['download_sessions_web'] = []  
            self.topologyGraph.node[node]['upload_pserver_sessions'] = 0
            
            #self.topologyGraph.node[node]['download_sessions_proxy'] = []   
            self.topologyGraph.node[node]['upload_remote_sessions'] = []   
          
            
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
   
     #this function is for corresponding an IP to a client of the topology    
    def setClientsIP(self,ip_list):
        if self.dataset=='IRCache':
            ips = copy.deepcopy(ip_list)
            nets=list(ips.keys())
            net_num = 0
            for seeker in self.seeker_nodes:
                net_key = nets[net_num]
                print(len(ips[net_key]))
                n_hosts = 0
                for switch in self.topologyGraph.neighbors(seeker):
                    if self.topologyGraph.node[switch]['tier']=='edge':
                        for host in self.topologyGraph.neighbors(switch):
                            if self.topologyGraph.node[host]['type']=='host' and len(ips[net_key])>0:
                                self.topologyGraph.node[host]['ip'] = ips[net_key].pop(0)
                                self.clientIDs[self.topologyGraph.node[host]['ip']] = host
                                self.topologyGraph.node[host]['seeker'] = seeker
                                self.topologyGraph.node[host]['switch'] = switch
                                n_hosts += 1
                redundancy = 2*math.ceil(math.log(n_hosts,2))
                self.topologyGraph.node[seeker]['max_redundancy'] = redundancy
                
                net_num += 1            
        else:
            iplist = copy.deepcopy(ip_list['berkeley'])
            iplist.sort()
            for seeker in self.seeker_nodes:
                n_hosts = 0
                for switch in self.topologyGraph.neighbors(seeker):
                    if self.topologyGraph.node[switch]['tier']=='edge':
                        for host in self.topologyGraph.neighbors(switch):
                            if self.topologyGraph.node[host]['type']=='host' and len(iplist)>0:
                                self.topologyGraph.node[host]['ip'] = iplist.pop(0)
                                self.clientIDs[self.topologyGraph.node[host]['ip']] = host
                                self.topologyGraph.node[host]['seeker'] = seeker
                                self.topologyGraph.node[host]['switch'] = switch
                                n_hosts += 1
                redundancy = 2*math.ceil(math.log(n_hosts,2))
                self.topologyGraph.node[seeker]['max_redundancy'] = redundancy
                        
        #print (self.clientIDs)
    
    def estimate_client_server_bw_pureweb(self,timestamp, bw, clientID,seekerID):
        #first remove finished sessions from download_sessions
        for r in self.topologyGraph.node[clientID]['download_sessions_web']:
            if r==-1:
                break
            elif r<timestamp:
                self.topologyGraph.node[clientID]['download_sessions_web'].remove(r)
            
        for r in self.topologyGraph.node[seekerID]['download_sessions_web']:
            if r<timestamp:
                self.topologyGraph.node[seekerID]['download_sessions_web'].remove(r)
            
        if len(self.topologyGraph.node[seekerID]['download_sessions_web'])>0:
            ex_bw = self.external_bw / float(len(self.topologyGraph.node[seekerID]['download_sessions_web']))
        else:
            ex_bw = self.external_bw 
        if len(self.topologyGraph.node[clientID]['download_sessions_web'])>0:
            local_bw = self.bw_client_download/float(len(self.topologyGraph.node[clientID]['download_sessions_web']))
        else:
            local_bw = self.bw_client_download
            
        if bw>0:
            return min([ex_bw,local_bw,bw])
        else:
            return min([ex_bw,local_bw])
#        return local_bw
                
    def compute_purewebTime(self, req):
        newReq = req
        clientID = self.clientIDs[req.clientIP]     
        seekerID = self.topologyGraph.node[clientID]['seeker']
        bw = self.estimate_client_server_bw_pureweb(req.timestamp, req.bw, clientID,seekerID)
        newReq.latency = req.rtt + 2*self.delay_client_seeker + req.responseLen/bw
        finish_time = req.timestamp + newReq.latency
        self.topologyGraph.node[clientID]['download_sessions_web'].insert(0,finish_time)
        self.topologyGraph.node[seekerID]['download_sessions_web'].insert(0,finish_time)
        self.results.add_pureweb(newReq.timestamp, newReq.reqID,newReq.URL,newReq.responseLen,newReq.latency)
        req.latency = newReq.latency
        return newReq        
        
    def compute_proxy_time(self, req):
        self.simulate_proxy(req)
        
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
                        self.results.add_Hit(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],tfinished_early-s['start_timestamp']+self.request_pserver_time,s['webserver_latency'])
                        self.register_in_local_host(s['clientID'],s['URL'],s['total_size'],tfinished_early)                        
                    else:
                        if self.results.add_miss(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],tfinished_early-s['start_timestamp']+self.request_pserver_time,s['webserver_latency'],1) is True:
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
     
      
    def addPserver_uploadSession(self, req, lastTimestamp, seekerID,clientID, Hit):
        available_BW_pserver = self.bw_pserver_upload/float(len(self.topologyGraph.node[seekerID]['upload_sessions'])+1)
        available_BW_peer = self.bw_client_pserver/float(self.topologyGraph.node[clientID]['upload_pserver_sessions']+1)
        self.topologyGraph.node[seekerID]['available_uploadBW'] = available_BW_pserver
        if available_BW_peer<available_BW_pserver:
            available_BW = available_BW_peer
        else:
            available_BW = available_BW_pserver
        newsession = {'reqID':req.reqID, 'URL':req.URL, 'total_size':req.responseLen,'webserver_latency':req.latency, 'retreived_size':0,'start_timestamp':req.timestamp,\
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
        
    
    def register_in_pserver(self, seekerID, url, dataLen,timestamp):
        
        self.topologyGraph.node[seekerID]['cacheSize'] = dataLen + self.topologyGraph.node[seekerID]['cacheSize']
        self.topologyGraph.node[seekerID]['cache'][url] = [url,dataLen,timestamp]
        self.topologyGraph.node[seekerID]['lru'][url] = self.topologyGraph.node[seekerID]['tm']
        self.topologyGraph.node[seekerID]['tm'] += 1
            
    def simulate_berkeley_proxy(self, req):
        clientID = self.clientIDs[req.clientIP]
        #print 'clientID'           
        #print clientID
        seekerID = self.topologyGraph.node[clientID]['seeker']
        if self.check_in_localCache_CDN(req,clientID):
            self.results.add_localDL_CDN(req.timestamp, req.reqID,req.URL,req.responseLen)
            self.local_foundnum_CDN = self.local_foundnum_CDN + 1
            return [clientID, 0]
        #print seekerID
        if req.URL in self.topologyGraph.node[seekerID]['cache'].keys():
            cacheElement = self.topologyGraph.node[seekerID]['cache'][req.URL]
            if cacheElement[2]<=req.timestamp:
                self.topologyGraph.node[seekerID]['lru'][req.URL] = self.topologyGraph.node[seekerID]['tm']
                self.topologyGraph.node[seekerID]['tm'] = self.topologyGraph.node[seekerID]['tm'] + 1
                #cacheElement = self.topologyGraph.node[seekerID]['cache'][req.URL]
                self.checkPserver_uploadSessions(req.timestamp,seekerID)
                self.addPserver_uploadSession(req, req.timestamp , seekerID,clientID,True)
                self.CDN_Hit = self.CDN_Hit + 1
                return
                
        bw = self.estimate_client_server_bw_pureweb(req.timestamp, req.bw, clientID,seekerID)
        latency_to_pserver = req.responseLen/bw + req.rtt
        estimatedResponseTime = latency_to_pserver + self.delay_client_pserver+self.request_pserver_time        
        self.register_in_pserver(seekerID,req.URL,req.responseLen,req.timestamp+req.latency)
        if self.results.add_miss(req.timestamp,req.reqID,req.URL,req.responseLen,estimatedResponseTime,latency_to_pserver,0) is True:
            self.register_in_local_host(clientID,req.URL,req.responseLen,req.timestamp+estimatedResponseTime)
        self.checkPserver_uploadSessions(req.timestamp + self.request_pserver_time,seekerID)
        self.addPserver_uploadSession(req,req.timestamp + self.request_pserver_time,seekerID,clientID,False)
        
        
    def extract_ircache_proxy(self, req): 
        if req.proxy_provider.count('HIT')>0:
            self.results.add_Hit(req.timestamp,req.reqID,req.URL,req.responseLen,req.latency,0)
        elif req.proxy_provider.count('MISS')>0:
            self.results.add_miss(req.timestamp,req.reqID,req.URL,req.responseLen,req.latency,0,2)
            
    def register_in_local_host(self, clientID, url, dataLen,timestamp):
        size_class = abs(int(math.ceil(math.log(dataLen,2))))       
        #check if cache is not full
        freecache= self.host_MaxCacheSize-self.topologyGraph.node[clientID]['cdn_cacheSize']#self.getFreeCacheSize(clientID,timestamp)
        if freecache<dataLen:      
            if dataLen<self.host_MaxCacheSize:
                print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
                for sc in range(size_class,self.LRU_Q_LEN):
                    while freecache<dataLen and len(self.topologyGraph.node[clientID]['cdn_lru'][sc].keys())>0:
                        old_key = min(self.topologyGraph.node[clientID]['cdn_lru'][sc].keys(), key=lambda k:self.topologyGraph.node[clientID]['cdn_lru'][sc][k])
                                          
                        cacheElement = self.topologyGraph.node[clientID]['cdn_cache'].pop(old_key)
                        self.topologyGraph.node[clientID]['cdn_lru'][sc].pop(old_key)
                        self.topologyGraph.node[clientID]['cdn_cacheSize'] = self.topologyGraph.node[clientID]['cdn_cacheSize']-cacheElement[1]
                        freecache = freecache + cacheElement[1]
                        
                        
                    if freecache>=dataLen:
                        break
                            
        if freecache>=dataLen:
            self.topologyGraph.node[clientID]['cdn_cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cdn_cacheSize']
            self.topologyGraph.node[clientID]['cdn_cache'][url] = [url,dataLen,timestamp]
            #print(type(self.topologyGraph.node[clientID]['lru'][size_class]),size_class)
            self.topologyGraph.node[clientID]['cdn_lru'][size_class][url] = self.topologyGraph.node[clientID]['cdn_tm']
            self.topologyGraph.node[clientID]['cdn_tm'] += 1
            
            
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
#        if len(self.topologyGraph.node[peerID]['upload_sessions_s1'])>1:
##            print len(self.topologyGraph.node[peerID]['upload_sessions'])
#            print ('shared BW for local p2p s1 from '+self.topologyGraph.node[peerID]['ip'] + '= ',file=self.f)
#            for ss in self.topologyGraph.node[peerID]['upload_sessions_s1']:
#                print(ss['URL'],ss['BW'],ss['receiver_peer'],file=self.f)
        sessions = self.topologyGraph.node[peerID]['upload_sessions_s1']
        print ('number of upload sessions1 for ' + str(peerID) + ' ' +
            str(len(self.topologyGraph.node[peerID]['upload_sessions_s1'])),file=self.f)
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]
            recieverID = self.clientIDs[s['receiver_peer']] 
            print('number of download sessions for '+ str(recieverID) +' ' +
                str(len(self.topologyGraph.node[recieverID]['download_sessions'])),file=self.f)
            for r in self.topologyGraph.node[recieverID]['download_sessions']:
                if r==-1:
                    break
                elif r<timestamp:
                    self.topologyGraph.node[recieverID]['download_sessions'].remove(r)
                    
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            #print(len(self.topologyGraph.node[peerID]['upload_sessions_s1']),file=self.f)
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                    self.topologyGraph.node[recieverID]['download_sessions'].pop()
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],tfinished_early)
                    self.topologyGraph.node[peerID]['upload_sessions_s1'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if s['reqID']>0:
                        if rtime>s['hhead_overhead']:
                            self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],True)
                        else:
                            self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,True)
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                    
                    if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                        down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
                    else:
                        down_bw = self.bw_client_download
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_uploadBW_s1'],down_bw)
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
            recieverID = self.clientIDs[s['receiver_peer']] 
            if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
            else:
                down_bw = self.bw_client_download
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_uploadBW_s1'],down_bw)
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['last_time']=timestamp
            self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']
            if self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']:
                self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s1'][i]['total_size']
                
    
    def checkLocalSessions_s2(self, timestamp, peerID):
        #at first remove each finished upload and update the BW
        #sessions = self.topologyGraph.node[peerID]['upload_sessions']
#        if len(self.topologyGraph.node[peerID]['upload_sessions_s2'])>1:
##            print len(self.topologyGraph.node[peerID]['upload_sessions'])
#            print ('shared BW for local p2p s2 from '+str(peerID) + '= '+
#              str(self.topologyGraph.node[peerID]['upload_sessions_s2'][0]['BW']),file=self.f)
#            print ('number of upload from :' + str(peerID) + '= '+
#              str(len(self.topologyGraph.node[peerID]['upload_sessions_s2'])),file=self.f)
        sessions = self.topologyGraph.node[peerID]['upload_sessions_s2']
        print ('number of upload sessions2 for ' + str(peerID) + ' ' +
            str(len(self.topologyGraph.node[peerID]['upload_sessions_s2'])),file=self.f)
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]
            recieverID = self.clientIDs[s['receiver_peer']] 
            print('number of download sessions for '+ str(recieverID) +' ' +
                str(len(self.topologyGraph.node[recieverID]['download_sessions'])),file=self.f)
            for r in self.topologyGraph.node[recieverID]['download_sessions']:
                if r==-1:
                    break
                elif r<timestamp:
                    self.topologyGraph.node[recieverID]['download_sessions'].remove(r)
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
#            print(len(self.topologyGraph.node[peerID]['upload_sessions_s2']),file=self.f)
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                    self.topologyGraph.node[recieverID]['download_sessions'].pop()
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],tfinished_early)
                    self.topologyGraph.node[peerID]['upload_sessions_s2'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if s['reqID']>0:
                        if rtime>s['hhead_overhead']:
                            self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],True)
                        else:
                            self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,True)
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                    
                    if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                        down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
                    else:
                        down_bw = self.bw_client_download
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_uploadBW_s2'],down_bw)
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
            recieverID = self.clientIDs[s['receiver_peer']] 
     
            if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
            else:
                down_bw = self.bw_client_download
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_uploadBW_s2'],down_bw)
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['last_time']=timestamp
            self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']=retreived_size + \
                    self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']
            if self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size']>self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']:
                self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['retreived_size'] = self.topologyGraph.node[peerID]['upload_sessions_s2'][i]['total_size']              
                  
    def checkRemoteSessions(self, timestamp, peerID):
        sessions = self.topologyGraph.node[peerID]['upload_remote_sessions']
        print ('number of upload remote sessions for ' + str(peerID) + ' ' +
            str(len(self.topologyGraph.node[peerID]['upload_remote_sessions'])),file=self.f)
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
            recieverID = self.clientIDs[s['receiver_peer']] 
            print('number of download sessions for '+ str(recieverID) +' ' +
                str(len(self.topologyGraph.node[recieverID]['download_sessions'])),file=self.f)
        for i in range(len(sessions)):
            s = self.topologyGraph.node[peerID]['upload_remote_sessions'][i]
            recieverID = self.clientIDs[s['receiver_peer']] 
            for r in self.topologyGraph.node[recieverID]['download_sessions']:
                if r==-1:
                    break
                elif r<timestamp:
                    self.topologyGraph.node[recieverID]['download_sessions'].remove(r)
        #at first remove each finished upload and update the BW
 
        while True:
            #find the first upload that is finished until timestamp
            i = 0
            i_early = []
            tfinished_early = timestamp
            print(len(self.topologyGraph.node[peerID]['upload_remote_sessions']),file=self.f)
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                    self.topologyGraph.node[recieverID]['download_sessions'].pop()
                    self.register(s['receiver_peer'], s['URL'], s['total_size'],t+s['last_time'])
                    self.topologyGraph.node[peerID]['upload_remote_sessions'].pop(i)
                    #register finished req log 
                    rtime = tfinished_early-s['start_timestamp']
                    if rtime>s['hhead_overhead']:                    
                        self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],rtime,s['overhead'],False)
                    else:
                        self.results.add_peerDL(s['start_timestamp'],s['reqID'],s['URL'],s['total_size'],s['hhead_overhead'],s['overhead']+s['hhead_overhead']-rtime,False)
                    
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
                    recieverID = self.clientIDs[s['receiver_peer']] 
                   
                    if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                        down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
                    else:
                        down_bw = self.bw_client_download
                    self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_remote_uploadBW'],down_bw)
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
            recieverID = self.clientIDs[s['receiver_peer']] 
            if len(self.topologyGraph.node[recieverID]['download_sessions'])>0:
                down_bw = self.bw_client_download/float(len(self.topologyGraph.node[recieverID]['download_sessions']))
            else:
                down_bw = self.bw_client_download
            self.topologyGraph.node[peerID]['upload_remote_sessions'][i]['BW'] = min(self.topologyGraph.node[peerID]['available_remote_uploadBW'],down_bw)
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
   
                    
    #{receiver_peer, isLocalPeer, URL, total_size,retreived_size,start_timestamp,last_time,BW}
    def addRemoteSession(self, req, clientID, lastTimestamp, providerPeer, overhead,hhead_overhead):
        if len(self.topologyGraph.node[clientID]['download_sessions'])>0:
            down_bw = self.bw_client_download/float(len(self.topologyGraph.node[clientID]['download_sessions']))
        else:
            down_bw = self.bw_client_download
        
        available_BW = self.bw_p2p_remote_upload/float(len(self.topologyGraph.node[providerPeer]['upload_remote_sessions'])+1)
        BW_session = min(available_BW,down_bw)
        self.topologyGraph.node[providerPeer]['available_remote_uploadBW'] = available_BW;
        newsession = {'receiver_peer':req.clientIP,'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':BW_session,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_remote_sessions'].append(newsession)
        self.topologyGraph.node[clientID]['download_sessions'].append(-1)
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_remote_sessions'])):
            self.topologyGraph.node[providerPeer]['upload_remote_sessions'][i]['BW'] = available_BW
            
    def addLocalSession_s1(self, req, clientID, lastTimestamp, providerPeer, overhead, hhead_overhead):
        if len(self.topologyGraph.node[clientID]['download_sessions'])>0:
            down_bw = self.bw_client_download/float(len(self.topologyGraph.node[clientID]['download_sessions']))
        else:
            down_bw = self.bw_client_download
        available_BW = self.bw_p2p_upload_layer1/float(len(self.topologyGraph.node[providerPeer]['upload_sessions_s1'])+1)
        BW_session = min(available_BW,down_bw)
        self.topologyGraph.node[providerPeer]['available_uploadBW_s1'] = available_BW;
        
        newsession = {'receiver_peer':req.clientIP, 'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':BW_session,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_sessions_s1'].append(newsession)
        self.topologyGraph.node[clientID]['download_sessions'].append(-1)
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_sessions_s1'])):
            self.topologyGraph.node[providerPeer]['upload_sessions_s1'][i]['BW'] = available_BW
    
    def addLocalSession_s2(self, req, clientID, lastTimestamp, providerPeer, overhead, hhead_overhead):
        if len(self.topologyGraph.node[clientID]['download_sessions'])>0:
            down_bw = self.bw_client_download/float(len(self.topologyGraph.node[clientID]['download_sessions']))
        else:
            down_bw = self.bw_client_download
        available_BW = self.bw_p2p_upload_layer2/float(len(self.topologyGraph.node[providerPeer]['upload_sessions_s2'])+1)
        BW_session = min(available_BW,down_bw)
        self.topologyGraph.node[providerPeer]['available_uploadBW_s2'] = available_BW;
        newsession = {'receiver_peer':req.clientIP, 'reqID':req.reqID,'URL':req.URL, 'total_size':req.responseLen,'overhead':overhead,\
                          'retreived_size':0,'start_timestamp':req.timestamp,'last_time':lastTimestamp,'BW':BW_session,'hhead_overhead':hhead_overhead}
        self.topologyGraph.node[providerPeer]['upload_sessions_s2'].append(newsession)
        self.topologyGraph.node[clientID]['download_sessions'].append(-1)
        #update BW of all the live session for selectedpeer             
        for i in range(len(self.topologyGraph.node[providerPeer]['upload_sessions_s2'])):
            self.topologyGraph.node[providerPeer]['upload_sessions_s2'][i]['BW'] = available_BW
       
    
    def check_in_localCache_CDN(self,req,clientID):
        size_class = abs(int(math.ceil(math.log(req.responseLen,2))) -1   )
        if req.URL in self.topologyGraph.node[clientID]['cdn_cache'].keys():
            cacheElement = self.topologyGraph.node[clientID]['cdn_cache'][req.URL]
            if cacheElement[2]<=req.timestamp:
                self.topologyGraph.node[clientID]['cdn_lru'][size_class][req.URL] = self.topologyGraph.node[clientID]['cdn_tm']
                self.topologyGraph.node[clientID]['cdn_tm'] = self.topologyGraph.node[clientID]['cdn_tm'] + 1
                return True
        return False        
     
    def check_in_localCache(self,req,clientID):
        size_class = abs(int(math.ceil(math.log(req.responseLen,2))) -1   )
        if req.URL in self.topologyGraph.node[clientID]['cache'].keys():
            cacheElement = self.topologyGraph.node[clientID]['cache'][req.URL]
            if cacheElement[2]<=req.timestamp:
                self.topologyGraph.node[clientID]['lru'][size_class][req.URL] = self.topologyGraph.node[clientID]['tm']
                self.topologyGraph.node[clientID]['tm'] = self.topologyGraph.node[clientID]['tm'] + 1
                return True
        return False         
             
    def estimate_client_server_bw(self,timestamp, bw, clientID,seekerID):
        #first remove finished sessions from download_sessions
        
        n=0
        for r in self.topologyGraph.node[clientID]['download_sessions']:
            if r==-1:
                break
            elif r<timestamp:
                self.topologyGraph.node[clientID]['download_sessions'].remove(r)
                n+=1
        print('client downloads: '+str(n),file=self.f)
        n=0    
        for r in self.topologyGraph.node[seekerID]['download_sessions']:
            if r<timestamp:
                self.topologyGraph.node[seekerID]['download_sessions'].remove(r)
                n +=1
        print('main switch downloads: '+str(n),file=self.f)
            
        if len(self.topologyGraph.node[seekerID]['download_sessions'])>0:
            ex_bw = self.external_bw / float(len(self.topologyGraph.node[seekerID]['download_sessions']))
        else:
            ex_bw = self.external_bw 
        if len(self.topologyGraph.node[clientID]['download_sessions'])>0:
            local_bw = self.bw_client_download/float(len(self.topologyGraph.node[clientID]['download_sessions']))
        else:
            local_bw = self.bw_client_download
        if bw>0:
            return min([ex_bw,local_bw,bw])
        else:
            return min([ex_bw,local_bw])
       # return local_bw
        
#    def add_to_pop_list(self,url):
#        self.url_reqNum.setdefault(url,0)
#        reqNum = self.url_reqNum[url]
#        if reqNum>0:
#            if self.reqNum_url[reqNum]==1:            
#                pop = self.reqNum_pop[reqNum]
#                self.pop_class.pop(pop)
#                
#                self.pop_class.remove(self.url_pop[url])
#                
#            mid = len(self.pop_class) / 2
#            found = False
#            while not found:
#                if self.url_reqNum[url]==self.pop_class[mid]:
        
            
    def update_reqRate(self, url):
        self.url_reqNum.setdefault(url,0)
        if self.url_reqNum[url]==0:
            self.url_reqNum[url]= 1
            self.reqNum.append(1)
            self.reqNum_index.setdefault(1,0)
            return
        pre_reqNum = self.url_reqNum[url]
        indx = self.reqNum_index[pre_reqNum]
        self.reqNum[indx] += 1
        if self.reqNum[indx+1]==pre_reqNum:
            self.reqNum_index[pre_reqNum] = indx + 1
        else:
            self.reqNum_index.pop(pre_reqNum)
        self.reqNum_index.setdefault(pre_reqNum+1,indx)
        self.url_reqNum[url] += 1
                    
    #this function seek a content in other peers
    #return [peerID,responseTime or seek time],
    #if a peer is found it return peerID and responseTime+seektime to get data from this peer
    #if no peer is found only seek time is returned with peerID=-1                
    def seek(self,req):#, bw_delay, web_responseTime):
        self.update_reqRate(req.URL)
        clientID = self.clientIDs[req.clientIP]     
        if self.check_in_localCache(req,clientID):
            self.results.add_localDL(req.timestamp, req.reqID,req.URL,req.responseLen)
            self.local_foundnum = self.local_foundnum + 1
            return [clientID, 0]
        size_class = abs(int(math.ceil(math.log(req.responseLen,2))) -1   )
        seekerID = self.topologyGraph.node[clientID]['seeker']
        #http_head_overhead = (self.httpHEAD_req_len+self.httpHEAD_response_len)/bw_delay[0]+2*bw_delay[1]  
        bw = self.estimate_client_server_bw(req.timestamp, req.bw, clientID,seekerID)
        http_head_overhead = (self.httpHEAD_response_len)/bw + req.rtt + 2*self.delay_client_seeker
        
        if len(self.topologyGraph.node[seekerID]['lookupTable'][req.URL])>0:       
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
                if req.URL in self.topologyGraph.node[selected_peer]['cache'].keys():
                    self.topologyGraph.node[selected_peer]['lru'][size_class][req.URL] = self.topologyGraph.node[selected_peer]['tm']
                    self.topologyGraph.node[selected_peer]['tm'] = self.topologyGraph.node[selected_peer]['tm'] + 1
                    
                overhead = self.seek_client_seeker_time+self.seekResponse_client_seeker_time# + http_head_overhead
                            
                #for peer in self.host_nodes:
                self.checkLocalSessions_s2(req.timestamp+overhead,selected_peer)
                self.checkLocalSessions_s1(req.timestamp+overhead,selected_peer)
                self.checkRemoteSessions(req.timestamp+overhead,selected_peer)
                if self.topologyGraph.node[selected_peer]['switch']==self.topologyGraph.node[clientID]['switch']:
                    self.addLocalSession_s1(req, clientID, req.timestamp + overhead, selected_peer,overhead,http_head_overhead)
                else:
                    self.addLocalSession_s2(req, clientID, req.timestamp + overhead, selected_peer,overhead,http_head_overhead)                    
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
            if len(self.topologyGraph.node[nseeker]['lookupTable'][req.URL])>0:   
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
            if req.URL in self.topologyGraph.node[selected_peer]['cache'].keys():
                self.topologyGraph.node[selected_peer]['lru'][size_class][req.URL] = self.topologyGraph.node[selected_peer]['tm']
                self.topologyGraph.node[selected_peer]['tm'] = self.topologyGraph.node[selected_peer]['tm'] + 1
                #for peer in self.host_nodes:
                #print ('find in remote peers')
            self.checkLocalSessions_s2(req.timestamp+overhead,selected_peer)
            self.checkLocalSessions_s1(req.timestamp+overhead,selected_peer)
            self.checkRemoteSessions(req.timestamp+overhead,selected_peer)
            self.addRemoteSession(req, clientID, req.timestamp+overhead,selected_peer, overhead,http_head_overhead)
            self.remotePeer_foundnum = self.remotePeer_foundnum + 1
            return [selected_peer,overhead]
            #else:
                #print 'retrive from remote peer is not accepted'
                #self.deniedPeerDL = self.deniedPeerDL + 1
        
        self.notFoundnum = self.notFoundnum + 1
        bw = self.estimate_client_server_bw(req.timestamp+overhead, req.bw, clientID,seekerID)
        req.latency = req.responseLen/bw + req.rtt + 2*self.delay_client_seeker
        self.results.add_webDL(req.timestamp,req.reqID, req.URL,req.responseLen,req.latency+overhead,overhead)
        finish_time = req.timestamp+req.latency+overhead
        self.topologyGraph.node[clientID]['download_sessions'].insert(0,finish_time)
        self.topologyGraph.node[seekerID]['download_sessions'].insert(0,finish_time)
        self.register(req.clientIP, req.URL, req.responseLen, finish_time)
        return [-1,overhead]

    def getFreeCacheSize(self,clientID, timestamp):
#        size = 0
#        print(len(self.topologyGraph.node[clientID]['cache'].values()),file=self.f)
#        for cache in self.topologyGraph.node[clientID]['cache'].values():
#            if cache[2]<=timestamp:
#                size = size + cache[1]
#        return self.host_MaxCacheSize-size          
        return self.host_MaxCacheSize-self.topologyGraph.node[clientID]['cacheSize']
        
   #register a content in cache
    def register_fullRedundant(self,clientIP, URL, dataLen,timestamp):
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']            
        size_class = abs(int(math.ceil(math.log(dataLen,2))) -1   )
        if size_class >= self.LRU_Q_LEN:
            return
        #check if cache is not full
        freecache= self.host_MaxCacheSize-self.topologyGraph.node[clientID]['cacheSize']#self.getFreeCacheSize(clientID,timestamp)
        if freecache<dataLen:      
            if dataLen<self.host_MaxCacheSize:
                print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
                #for sc in range(size_class,self.LRU_Q_LEN):
                for sc in range(size_class,0,-1):
                    while freecache<dataLen and len(self.topologyGraph.node[clientID]['lru'][sc].keys())>0:
                        old_key = min(self.topologyGraph.node[clientID]['lru'][sc].keys(), key=lambda k:self.topologyGraph.node[clientID]['lru'][sc][k])
                                          
                        cacheElement = self.topologyGraph.node[clientID]['cache'].pop(old_key)
                        self.topologyGraph.node[clientID]['lru'][sc].pop(old_key)
                        self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                        freecache = freecache + cacheElement[1]
                        i = 0
                        removed_URL = cacheElement[0]
                        while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                            if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                                self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                                break
                            i = i + 1
                    if freecache>=dataLen:
                        break
                            
        if freecache>=dataLen:
            self.topologyGraph.node[seekerID]['lookupTable'][URL].insert(0, {"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'][URL] = [URL,dataLen,timestamp]
            #print(type(self.topologyGraph.node[clientID]['lru'][size_class]),size_class)
            self.topologyGraph.node[clientID]['lru'][size_class][URL] = self.topologyGraph.node[clientID]['tm']
            self.topologyGraph.node[clientID]['tm'] += 1

                
    #register a content in cache
    def register_noRedundant(self,clientIP, URL, dataLen,timestamp):
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']  
        size_class = abs(int(math.ceil(math.log(dataLen,2))) -1   )
        if size_class >= self.LRU_Q_LEN:
            return
        if self.topologyGraph.node[seekerID]['lookupTable'][URL]!=None:
            if len(self.topologyGraph.node[seekerID]['lookupTable'][URL])>0:
                if self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['timestamp']>timestamp:
                    removedID = self.topologyGraph.node[seekerID]['lookupTable'][URL][0]['clientID']
                    if URL in self.topologyGraph.node[removedID]['cache'].keys():
                        self.topologyGraph.node[removedID]['cache'].pop(URL)
                        self.topologyGraph.node[removedID]['lru'][size_class].pop(URL)
                        self.topologyGraph.node[removedID]['cacheSize'] = self.topologyGraph.node[removedID]['cacheSize'] - dataLen
                        #self.topologyGraph.node[seekerID]['lookupTable'][URL].insert(0, {"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
                        
                else:
                    return	 
       
        freecache=self.getFreeCacheSize(clientID,timestamp)
        if freecache<dataLen: 
            if dataLen<self.host_MaxCacheSize:
                #print('peer: cache size: ' + str(self.topologyGraph.node[clientID]['cacheSize']),file=self.f)
#                print('peer: cache replacement',file=self.f)
                print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
                #for sc in range(size_class,self.LRU_Q_LEN):
                for sc in range(size_class,0,-1):
                    while freecache<dataLen and len(self.topologyGraph.node[clientID]['lru'][sc].keys())>0:
                        old_key = min(self.topologyGraph.node[clientID]['lru'][sc].keys(), key=lambda k:self.topologyGraph.node[clientID]['lru'][sc][k])
                        cacheElement = self.topologyGraph.node[clientID]['cache'].pop(old_key)
                        self.topologyGraph.node[clientID]['lru'][sc].pop(old_key)
                        self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                        freecache = freecache + cacheElement[1]
                        i = 0
                        removed_URL = cacheElement[0]
                        while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                            if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                                self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                                break
                            i = i + 1
                    if freecache>=dataLen:
                        break
                                            
        if(freecache>=dataLen):
            self.topologyGraph.node[seekerID]['lookupTable'][URL].insert(0, {"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'][URL] = [URL,dataLen,timestamp]
            #print(type(self.topologyGraph.node[clientID]['lru'][size_class]),size_class)
            self.topologyGraph.node[clientID]['lru'][size_class][URL] = self.topologyGraph.node[clientID]['tm']
            self.topologyGraph.node[clientID]['tm'] += 1

                
    def get_closeTime(self,timestamp):
        t1 = int(timestamp)
        self.time_reqNum.setdefault(t1,0)
        while(self.time_reqNum[t1]==0):
            t1 -= 1
            self.time_reqNum.setdefault(t1,0)
        return t1
    def register_popularityBased(self,clientIP, URL, dataLen,timestamp):
       
        clientID = self.clientIDs[clientIP]
        seekerID = self.topologyGraph.node[clientID]['seeker']   
        size_class = abs(int(math.ceil(math.log(dataLen,2))) -1   )
        if size_class >= self.LRU_Q_LEN:
            return
        available_redundancy = len(self.topologyGraph.node[seekerID]['lookupTable'][URL])
        if len(self.reqNum)==100000:
            print('reqNums:',self.reqNum,file=self.f )
            print('reqNum_index:',self.reqNum_index,file=self.f )
        if available_redundancy>=1:
            rate_ratio = self.reqNum_index[self.url_reqNum[URL]] / float(self.reqNum_index[self.reqNum[len(self.reqNum)-1]])
            cache_redundancy = 1+self.topologyGraph.node[seekerID]['max_redundancy']/float(1+math.exp((rate_ratio-0.5)/0.1))
            print("rate ratio:" + str( rate_ratio), file=self.f)            
            print ("cache redundancy for " + URL +': ' + str(cache_redundancy),file=self.f)
            if cache_redundancy<=available_redundancy:
                return	 
                       
        #check if cache is not full
        freecache=self.getFreeCacheSize(clientID,timestamp)
        if(freecache<dataLen):
            print ('peer: limited cache for dataLen: '+ str(dataLen),file=self.f)
            #for sc in range(size_class,self.LRU_Q_LEN):
            for sc in range(size_class,0,-1):
                while freecache<dataLen and len(self.topologyGraph.node[clientID]['lru'][sc].keys())>0:
                    old_key = min(self.topologyGraph.node[clientID]['lru'][sc].keys(), key=lambda k:self.topologyGraph.node[clientID]['lru'][sc][k])
                    cacheElement = self.topologyGraph.node[clientID]['cache'].pop(old_key)
                    self.topologyGraph.node[clientID]['lru'][sc].pop(old_key)
                    self.topologyGraph.node[clientID]['cacheSize'] = self.topologyGraph.node[clientID]['cacheSize']-cacheElement[1]
                    freecache = freecache + cacheElement[1]
                    i = 1
                    removed_URL = cacheElement[0]
                    while i <len(self.topologyGraph.node[seekerID]['lookupTable'][removed_URL]):
                        if self.topologyGraph.node[seekerID]['lookupTable'][removed_URL][i]['clientID']==clientID:
                            self.topologyGraph.node[seekerID]['lookupTable'][removed_URL].pop(i)
                            break
                        i = i + 1
                if freecache>=dataLen:
                    break
                                            
        if(freecache>=dataLen):
            self.topologyGraph.node[seekerID]['lookupTable'][URL].insert(1, {"clientID":clientID,"clientIP":clientIP,"timestamp":timestamp})
            self.topologyGraph.node[clientID]['cacheSize'] = dataLen + self.topologyGraph.node[clientID]['cacheSize']
            self.topologyGraph.node[clientID]['cache'][URL] = [URL,dataLen,timestamp]
            #print(type(self.topologyGraph.node[clientID]['lru'][size_class]),size_class)
            self.topologyGraph.node[clientID]['lru'][size_class][URL] = self.topologyGraph.node[clientID]['tm']
            self.topologyGraph.node[clientID]['tm'] += 1

           
if __name__=='__main__':
    t = Topology(4, 2, 20, 3,'1',100)
    nx.draw(t.topologyGraph)
   
    
