# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 12:33:39 2016

@author: Zeinab Zali

"""
from __future__ import print_function
from Topology import Topology
import os
#from stats import TruncatedZipfDist
from collections import defaultdict

class SimulatorGenerator(object):
        
    def __init__(self, dataset, logfolder , cache_size, aliveProb, cachePolicy, day=None):#, aliveProb, cache_policy, reqRate, distribution): # 1:fully_redundant, 2:no_redundant, 3: popularity_based):
        self.logFile = logfolder
        #self.cache_policy = cache_policy
        #self.logNum = logNum
        #self.aliveProb = aliveProb
        #list of dictionary[req_time, URL, responseTime(us), DL_speed, clientIP, ServerIP, responseDataLan, isSupported] sorted by req_time
        self.eventList = [] 
        self.contents = defaultdict(list)
        self.topology = None
        self.clientsIP = defaultdict()
        self.serversIP = set()
        self.URLs_list = []
        self.URLsNum = 0
        self.URLs_dict = defaultdict(dict)
        self.max_size = 0
        self.traffic_type=''
        self.avg_size = 0
        self.eventNum = 0
        self.eventFilePos = 0
        self.aliveProb = aliveProb
        self.cache_policy = cachePolicy
        self.trace_day = day
        self.cache_size = cache_size
        self.dataset = dataset
        if dataset=='IRCache':
            self.events_folder = self.logFile+'events_dir_'+self.trace_day + '/'
            self.outputPath = './output/' + dataset + '/dynamic'+ str(aliveProb) + '_' + \
            cachePolicy+'_cacheSize'+ str(cache_size/1000000) +'MB'+'/day_'+day + '/'
        else:
            self.events_folder = self.logFile+'events_dir/'
            self.outputPath = './output/' + dataset + '/dynamic'+ str(aliveProb) + '_' + \
            cachePolicy+'_cacheSize'+ str(cache_size/1000000) +'MB/'
        
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)
       
        
    def nextEventList(self):
        fevents = open(self.events_folder+ 'events.txt')
        fevents.seek(self.eventFilePos)
        events = []
        line = fevents.readline()
        i = 0
        while (line and i<100000):
            fields = line.rstrip().split(' ')
            if len(fields)>=10:
                if fields[9]=='True':
                    supported = True
                else:
                    supported = False
                
                e = {'timestamp':int(fields[0]),'URL':fields[1], 'responseLen':int(fields[2]),
                     'RTT':float(fields[3]), 'BW':float(fields[4]), 'responseTime':int(fields[5]),'clientIP':fields[6],
                     'serverIP':fields[7], 'proxy_provider': fields[8] ,'isSupported':supported}
                events.append(e)
                 #print (e)
            line = fevents.readline()
            i = i + 1
        self.eventFilePos = fevents.tell()-len(line)
        fevents.close()
        if len(events)>0:
            return events    
        return None
    
    def readClientsIP(self):
        #read clients IPs
        for filename in os.listdir(self.events_folder):
            if filename.startswith('clients'):
                ipList=[]
                f = open( self.events_folder + filename)
                line = f.readline()
                while line:
                    ipList.append(line.rstrip())
                    line = f.readline()
                f.close()
                self.clientsIP.setdefault(filename[8:],ipList)
        return self.clientsIP
        
    def defineClientsIP(self):
        #read clients IPs
        for filename in os.listdir(self.events_folder):
            if filename.startswith('clients'):
                ipList=[]
                f = open( self.events_folder + filename)
                line = f.readline()
                while line:
                    ipList.append(line.rstrip())
                    line = f.readline()
                f.close()
                self.clientsIP.setdefault(filename[8:],ipList)
        #define topology
        if self.dataset=='Berkeley':
            self.topology = Topology(self.dataset, 10,self.clientsIP,3,self.aliveProb, self.cache_policy,self.cache_size, self.outputPath)
        else:
            self.topology = Topology(self.dataset, 8,self.clientsIP,3,self.aliveProb, self.cache_policy,self.cache_size, self.outputPath)
        self.topology.setClientsIP(self.clientsIP)
           
    def printInfo(self,latency):
        if latency:
            f = open(self.outputPath+'info.txt','w')
        else:
            f = open(self.outputPath+'info_noLatency.txt','w')
        print ('*******PICN Simulation********', file=f)
        
        if latency:
            print ('Topology and traffic information:\n(client_seeker_BW:'+str(self.topology.bw_client_seeker*8/1000)+' Mb/s)',file=f)
            print ('(seeker_seeker_BW:'+str(self.topology.bw_seeker_seeker*8/1000)+' Mb/s)',file=f)
            print ('(local_p2p_uploadBW layer 1:'+str(self.topology.bw_p2p_upload_layer1*8/1000)+' Mb/s)',file=f)
            print ('(local_p2p_uploadBW layer 2:'+str(self.topology.bw_p2p_upload_layer2*8/1000)+' Mb/s)',file=f)
            print ('(remote_p2p_uploadBW:'+ str(self.topology.bw_p2p_remote_upload*8/1000)+' Mb/s)',file=f)
            #print ('(pserver_clinet_uploadBW:'+str(self.topology.bw_client_pserver)+' Mb/s) ',file=f)
            #print ('(pserver_uploadBW:'+str(self.topology.bw_pserver_upload)+' Mb/s) ',file=f)
            #print ('(pserver_downloadBW:'+str(self.topology.bw_pserver_download)+ ' Mb/s)',file=f)
            print ('(peers_cache_size:'+str(self.topology.host_MaxCacheSize/float(1000000))+' MB)',file=f)
            print ('Number of LANs:' + str(len(self.topology.seeker_nodes)),file=f)
        #print ('(pservers_cache_size:'+str(self.topology.pserver_MaxCacheSize/float(8000000))+' MB)\n',file=f)
        
        print (self.traffic_type,file=f)        
        
        #print ('Total request rate: ' + str(self.bigLambda), file=f)
        #print ('request rate for each client: ' + str(self.bigLambda/float(len(self.clientsIP))),file=f)
        clientNum = 0 
        for ip in self.clientsIP.keys():
            #print(self.clientsIP[ip],file=f)
            clientNum+= len(self.clientsIP[ip])
        print ('Total number of requests:' + str(self.eventNum),file=f)
        print ('Total number of supported requests:' + str(self.supportedNum),file=f)
        print ('Total number of clients:' + str(clientNum),file=f)
        print ('number of webservers:' + str(self.serversIPnum),file=f)
        print ('number of different URLs:' + str(self.URLsNum),file=f)
        print ('maximum size of contents: ' + str(self.max_size),file=f)
        print ('average size of contents: ' + str(self.avg_size) +'\n',file=f)
        
        f.close()
        
    def loadEvents(self, latency):
        fevents = open(self.events_folder + 'events_info.txt')
        line = fevents.readline().rstrip()
        self.traffic_type = line
        line = fevents.readline().rstrip()
        self.URLsNum = int(line)
        line = fevents.readline().rstrip()
        self.serversIPnum = int(line)
        line = fevents.readline().rstrip()
        self.max_size = int(line)
        line = fevents.readline().rstrip()
        self.avg_size = float(line)
        line = fevents.readline().rstrip()
        self.eventNum = int(line) 
        line = fevents.readline().rstrip()
        self.supportedNum = int(line) 
        self.eventFilePos = 0
        fevents.close()
        if latency:
            self.defineClientsIP()
        
