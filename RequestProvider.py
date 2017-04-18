# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 17:16:09 2017

@author: root
"""
import random
from collections import defaultdict
import math
import copy 

class RequestProvider(object):
   
    def __init__(self, dataset,clients, aliveProb, neighboring_prob, cache_policy, cache_size): 
        if cache_policy=='fully_redundant':
            self.register = self.register_fully_redundant
        elif cache_policy == 'no_redundant':
            self.register = self.register_no_redundant
        else:
            self.register = self.register_popularity_based
        self.CLIENT_MAX_CACHE_SIZE = cache_size#0.5 * 1000000000 #2GB
        self.aliveProb = aliveProb/float(100)
        self.clients = clients              #{seeker_id:[list of client ips]}
                
        self.seekers_lookupTab = dict()  #{seekerID:{url:[clientIPs]}}
        self.seekers_neighboring = dict()
        self.clients_cache = defaultdict()
        self.clients_seekerID = dict() #{clientIP:seekerID}
        self.LRU_Q_LEN = int(math.ceil(math.log(self.CLIENT_MAX_CACHE_SIZE+1,2)))
        prob = 1 / float(neighboring_prob)
        self.max_redundancy = dict()
        if dataset=='Berkeley':
            self.seekers = range(10)   
        else:
            self.seekers = self.clients.keys()
        
        for seeker in self.seekers:
            self.seekers_lookupTab.setdefault(seeker,defaultdict())
            self.seekers_lookupTab[seeker].setdefault('cache', defaultdict(list))  #{seekerID:{url:[clientIPs]}}
#            self.seekers_lookupTab[seeker].setdefault('tm', 0)
#            self.seekers_lookupTab[seeker].setdefault('lru', dict())
            self.seekers_neighboring.setdefault(seeker,set())
            for nseeker in self.seekers:
                r = random.random()
                print("random: "+str(r))
                if nseeker!=seeker and r<prob:
                    print("neighbor")
                    self.seekers_neighboring[seeker].add(nseeker)
        if dataset=='Berkeley':
            clients_b = copy.deepcopy(clients['berkeley'])
            i = 0
            local_peers_num = len(clients_b)/10+1
            self.clients = defaultdict(list)
            for seeker in self.seekers:
                self.clients.setdefault(seeker,[])
                for ci in range(i,i+local_peers_num):
                    if ci == len(clients_b):
                        break
                    c = clients_b[ci]
                    self.clients[seeker].append(c)
                    self.clients_cache.setdefault(c,defaultdict())
                    self.clients_cache[c].setdefault('freeCache', self.CLIENT_MAX_CACHE_SIZE)    #{clientIP:free_size}
                    self.clients_cache[c].setdefault('cache', defaultdict(int))  #{clientIP:{url:size}}
                    self.clients_cache[c].setdefault('tm', 0)
                    self.clients_cache[c].setdefault('lru',defaultdict())
                    for j in range(self.LRU_Q_LEN):
                        self.clients_cache[c]['lru'][j] = defaultdict(int)
                    self.clients_seekerID.setdefault(c,seeker) 
                    
                self.max_redundancy.setdefault(seeker,2*math.ceil(math.log(len(self.clients[seeker]),2))) 
                print(self.max_redundancy[seeker])
                i += local_peers_num
        else: 
            for seeker in self.seekers:
                self.max_redundancy.setdefault(seeker,2*math.ceil(math.log(len(self.clients[seeker]),2))) 
                print(self.max_redundancy[seeker])
                for c in self.clients[seeker]:
                    self.clients_cache.setdefault(c,defaultdict())
                    self.clients_cache[c].setdefault('freeCache', self.CLIENT_MAX_CACHE_SIZE)    #{clientIP:free_size}
                    self.clients_cache[c].setdefault('cache', defaultdict(int))  #{clientIP:{url:size}}
                    self.clients_cache[c].setdefault('tm', 0)
                    self.clients_cache[c].setdefault('lru',defaultdict())
                    for i in range(self.LRU_Q_LEN):
                        self.clients_cache[c]['lru'][i] = defaultdict(int)
                    self.clients_seekerID.setdefault(c,seeker)
                
        
        self.local_hit = 0 #number of hit in local cache
        self.p2p_hit = 0
        self.rp2p_hit = 0
        self.miss = 0
        self.local_hit_size = 0 #number of hit in local cache
        self.p2p_hit_size = 0
        self.rp2p_hit_size = 0
        self.miss_size = 0
        self.tot_size = 0
        self.reqNum = 0
                
    
    def register_fully_redundant(self, timestamp, clientIP, URL, responseLen):
        seeker_id = self.clients_seekerID[clientIP]
        size_class = int(math.floor(math.log(responseLen,2)))   
        if self.CLIENT_MAX_CACHE_SIZE > responseLen:        
            if (self.clients_cache[clientIP]['freeCache']<responseLen):
                for sc in range(size_class,self.LRU_Q_LEN):
                    while self.clients_cache[clientIP]['freeCache']<responseLen and len(self.clients_cache[clientIP]['lru'][sc].keys())>0:
#                print(self.clients_cache[clientIP]['freeCache'],responseLen)
                        old_key = min(self.clients_cache[clientIP]['lru'][sc].keys(), key=lambda k:self.clients_cache[clientIP]['lru'][sc][k])
                        cacheElement = self.clients_cache[clientIP]['cache'].pop(old_key)
                        self.clients_cache[clientIP]['lru'][sc].pop(old_key)
                        self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache']+cacheElement
                        i = 0
                        while i <len(self.seekers_lookupTab[seeker_id]['cache'][old_key]):
                            if self.seekers_lookupTab[seeker_id]['cache'][old_key][i]==clientIP:
                                self.seekers_lookupTab[seeker_id]['cache'][old_key].pop(i)
                                break
                            i = i + 1            
                #print('cache is available now')
                
            if (self.clients_cache[clientIP]['freeCache']>=responseLen):
                self.clients_cache[clientIP]['cache'][URL] = responseLen
                self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache'] - responseLen
                self.clients_cache[clientIP]['lru'][size_class][URL] = self.clients_cache[clientIP]['tm']
                self.clients_cache[clientIP]['tm'] += 1
                self.seekers_lookupTab[seeker_id]['cache'][URL].append(clientIP)
                
                
    def register_no_redundant(self, timestamp, clientIP, URL, responseLen):
        seeker_id = self.clients_seekerID[clientIP]
        size_class = int(math.floor(math.log(responseLen,2)))  
        if len(self.seekers_lookupTab[seeker_id]['cache'][URL])>0:
            return
        if self.CLIENT_MAX_CACHE_SIZE > responseLen:        
            if (self.clients_cache[clientIP]['freeCache']<responseLen):
                for sc in range(size_class,self.LRU_Q_LEN):
                    while self.clients_cache[clientIP]['freeCache']<responseLen and len(self.clients_cache[clientIP]['lru'][sc].keys())>0:
#                print(self.clients_cache[clientIP]['freeCache'],responseLen)
                        old_key = min(self.clients_cache[clientIP]['lru'][sc].keys(), key=lambda k:self.clients_cache[clientIP]['lru'][sc][k])
                        cacheElement = self.clients_cache[clientIP]['cache'].pop(old_key)
                        self.clients_cache[clientIP]['lru'][sc].pop(old_key)
                        self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache']+cacheElement
                        i = 0
                        while i <len(self.seekers_lookupTab[seeker_id]['cache'][old_key]):
                            if self.seekers_lookupTab[seeker_id]['cache'][old_key][i]==clientIP:
                                self.seekers_lookupTab[seeker_id]['cache'][old_key].pop(i)
                                break
                            i = i + 1            
                #print('cache is available now')
                
            if (self.clients_cache[clientIP]['freeCache']>=responseLen):
                self.clients_cache[clientIP]['cache'][URL] = responseLen
                self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache'] - responseLen
                self.clients_cache[clientIP]['lru'][size_class][URL] = self.clients_cache[clientIP]['tm']
                self.clients_cache[clientIP]['tm'] += 1
                self.seekers_lookupTab[seeker_id]['cache'][URL].append(clientIP)
                
    def register_popularity_based(self, timestamp, clientIP, URL, responseLen):
        seeker_id = self.clients_seekerID[clientIP]
        size_class = int(math.floor(math.log(responseLen,2)))  
        available_redundancy = len(self.seekers_lookupTab[seeker_id]['cache'][URL])-1
        if available_redundancy>=0:
            first_time = self.seekers_lookupTab[seeker_id]['cache'][URL][0]['timestamp']
            req_num = self.seekers_lookupTab[seeker_id]['cache'][URL][0]['req_num']
            if (timestamp-first_time)<=0:
                r = req_num/float(1)*100
            else:
                r = req_num/float(timestamp-first_time)*100
            cache_redundancy = round(r*self.max_redundancy[seeker_id],0)
            print ("cache redundancy: "+str(cache_redundancy))
            if cache_redundancy<=available_redundancy:
                return	 
        else:
            self.seekers_lookupTab[seeker_id]['cache'][URL].insert(0,{'timestamp':timestamp,'req_num':1})
        if self.CLIENT_MAX_CACHE_SIZE > responseLen:        
            if (self.clients_cache[clientIP]['freeCache']<responseLen):
                for sc in range(size_class,self.LRU_Q_LEN):
                    while self.clients_cache[clientIP]['freeCache']<responseLen and len(self.clients_cache[clientIP]['lru'][sc].keys())>0:
#                print(self.clients_cache[clientIP]['freeCache'],responseLen)
                        old_key = min(self.clients_cache[clientIP]['lru'][sc].keys(), key=lambda k:self.clients_cache[clientIP]['lru'][sc][k])
                        cacheElement = self.clients_cache[clientIP]['cache'].pop(old_key)
                        self.clients_cache[clientIP]['lru'][sc].pop(old_key)
                        self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache']+cacheElement
                        i = 0
                        while i <len(self.seekers_lookupTab[seeker_id]['cache'][old_key]):
                            if self.seekers_lookupTab[seeker_id]['cache'][old_key][i]==clientIP:
                                self.seekers_lookupTab[seeker_id]['cache'][old_key].pop(i)
                                break
                            i = i + 1            
            #print('cache is available now')
            
        if (self.clients_cache[clientIP]['freeCache']>=responseLen):
            self.clients_cache[clientIP]['cache'][URL] = responseLen
            self.clients_cache[clientIP]['freeCache'] = self.clients_cache[clientIP]['freeCache'] - responseLen
            self.clients_cache[clientIP]['lru'][size_class][URL] = self.clients_cache[clientIP]['tm']
            self.clients_cache[clientIP]['tm'] += 1
            self.seekers_lookupTab[seeker_id]['cache'][URL].append(clientIP)
    
    def is_alive(self, clientIP):
        if random.random()<self.aliveProb:
            return True
        return False
        
    def seek(self, req):
        self.reqNum += 1
        self.tot_size += req.responseLen
        size_class = int(math.floor(math.log(req.responseLen,2)))  
        if self.clients_cache[req.clientIP]['cache'][req.URL]>0:
            #print('hit in local')
            self.clients_cache[req.clientIP]['lru'][size_class][req.URL] = self.clients_cache[req.clientIP]['tm']
            self.clients_cache[req.clientIP]['tm'] += 1
            self.local_hit +=1
            self.local_hit_size += req.responseLen
            return
        seeker_id = self.clients_seekerID[req.clientIP]
        if len(self.seekers_lookupTab[seeker_id]['cache'][req.URL])>0:
            if type(self.seekers_lookupTab[seeker_id]['cache'][req.URL][0])==dict:
                self.seekers_lookupTab[seeker_id]['cache'][req.URL][0]['req_num']+= 1
                d = 1
            else:
                d = 0
            for client in self.seekers_lookupTab[seeker_id]['cache'][req.URL][d:]:
                if self.is_alive(client):
                    self.p2p_hit +=1
                    self.p2p_hit_size += req.responseLen
                    self.register(req.timestamp, req.clientIP, req.URL, req.responseLen)
                    self.clients_cache[client]['lru'][size_class][req.URL] = self.clients_cache[client]['tm']
                    self.clients_cache[client]['tm'] += 1
                    return
        for nseeker in self.seekers_neighboring[seeker_id]:
            #print("neighbor: " + str(nseeker))
            if len(self.seekers_lookupTab[nseeker]['cache'][req.URL])>0:
                if type(self.seekers_lookupTab[nseeker]['cache'][req.URL][0])==dict:
                    self.seekers_lookupTab[nseeker]['cache'][req.URL][0]['req_num']+= 1
                    d = 1
                else:
                    d = 0
                for client in self.seekers_lookupTab[nseeker]['cache'][req.URL][d:]:
                    if self.is_alive(client):
                        self.rp2p_hit +=1
                        self.rp2p_hit_size += req.responseLen
                        self.register(req.timestamp, req.clientIP, req.URL, req.responseLen)
                        self.clients_cache[client]['lru'][size_class][req.URL] = self.clients_cache[client]['tm']
                        self.clients_cache[client]['tm'] += 1
                        return
        
        self.miss += 1 
        self.miss_size += req.responseLen
        self.register(req.timestamp, req.clientIP, req.URL, req.responseLen)
        
                    