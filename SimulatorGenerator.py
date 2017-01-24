# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 12:33:39 2016

@author: Zeinab Zali

"""
from __future__ import print_function
import sys
from Topology import Topology
import os
from stats import TruncatedZipfDist
from collections import defaultdict
import random
import math
from optparse import OptionParser

class SimulatorGenerator(object):
        
    def __init__(self, logFile, aliveProb, cache_policy): # 1:fully_redundant, 2:no_redundant, 3: popularity_based):
        self.logFile = logFile
        self.cache_policy = cache_policy
        #self.logNum = logNum
        self.aliveProb = aliveProb
        #list of dictionary[req_time, URL, responseTime(us), DL_speed, clientIP, ServerIP, responseDataLan, isSupported] sorted by req_time
        self.eventList = [] 
        self.contents = defaultdict(list)
        self.topology = None
        self.clientsIP = set()
        self.serversIP = set()
        self.URLs_list = []
        self.URLsNum = 0
        self.URLs_dict = defaultdict(dict)
        self.max_size = 0
        self.bigLambda = 0
        self.alpha = 0
        self.traffic_type=''
        self.avg_size = 0
        self.eventNum = 0
        self.eventFilePos = 0
        
        
    def nextEvent(self):
        if len(self.eventList)>0:
            return self.eventList.pop(0)
        outputPath = './output/' + 'dynamic_'+str(self.aliveProb) + '_' + policy+'/'
        fevents = open(outputPath+'events.txt')
        fevents.seek(self.eventFilePos)
        line = fevents.readline()
        i = 0
        while (line and i<100000):
            fields = line.split(' ')
            if len(fields)>=8:
                 e = {'timestamp':int(fields[0]),'URL':fields[1], 'responseTime':int(fields[2]),\
                 'DL_speed':float(fields[3]),'clientIP':fields[4],\
                 'serverIP':fields[5],'responseLen':int(fields[6]),'isSupported':bool(fields[7])}
                 self.eventList.append(e)
                 #print (e)
            line = fevents.readline()
            i = i + 1
        self.eventFilePos = fevents.tell()-len(line)
        fevents.close()
        if len(self.eventList)>0:
            return self.eventList.pop(0)    
        return None

    def nextEventList(self):
        outputPath = './output/' + 'dynamic_'+str(self.aliveProb) + '_' + self.cache_policy+'/'
        fevents = open(outputPath+'events.txt')
        fevents.seek(self.eventFilePos)
        events = []
        line = fevents.readline()
        i = 0
        while (line and i<100000):
            fields = line.split(' ')
            if len(fields)>=8:
                 e = {'timestamp':int(fields[0]),'URL':fields[1], 'responseTime':int(fields[2]),\
                 'DL_speed':float(fields[3]),'clientIP':fields[4],\
                 'serverIP':fields[5],'responseLen':int(fields[6]),'isSupported':bool(fields[7])}
                 events.append(e)
                 #print (e)
            line = fevents.readline()
            i = i + 1
        self.eventFilePos = fevents.tell()-len(line)
        fevents.close()
        if len(events)>0:
            return events    
        return None
        
    def getKey(self,req):
        return req['timestamp']
    
    def str2timestamp(self,str):
        f = str.split(":")
        return int(f[0])*1000000+int(f[1])
        
    def defineClientsIP(self):
        ipList = list(self.clientsIP)        
        ipList.sort(reverse=True);
        #10 seekers
        
        self.topology = Topology(10,20,len(ipList),3,self.aliveProb, self.cache_policy)
        self.topology.setClientsIP(ipList)

        
    def generate_zipf_traffic(self,alpha,rate):
        self.alpha = alpha
        self.bigLambda = rate
        print ("generating zipf traffic",file=sys.stdout)
        f = open(self.logFile+'/trace_detail_1')
        size_sum = 0
        supported = 0
        ## Read the first line 
        line = f.readline()
        #print (line)
        # If the file is not empty keep reading line one at a time
        # till the file is empty
        while line:
            #fields = [req_time,firstByteTime,LastByteTime,clientIP,ServerIP,clientHeader,
            #ServerHeader,IfModefinedSinceClientHeader,ExpiresServerHeader, LastModefiedServerHeader,responseHeaderLen,
            #responseDataLan,URLLen, GET, URLValue, HTTP/1.0]
            fields = line.split(" ")
            #if the request is not GET request deny it
            
            if fields[13]=='GET':
                #compute response time in microseconds
                responseLen = (int(fields[11])+int(fields[10]))
                if responseLen<500000:
                    responseLen = responseLen * 800
                elif responseLen<1000000:
                    responseLen = responseLen * 80
                else:
                    responseLen = responseLen * 8
                if responseLen>0:
                    start_dt = self.str2timestamp(fields[0])
                    end_dt = self.str2timestamp(fields[2])
                    responseTime = end_dt - start_dt
                    ip = fields[3].split(":")[0]
                    timestamp = self.str2timestamp(fields[0])
                    self.clientsIP.add(ip)
                    self.serversIP.add(fields[4].split(":")[0])
                    url = fields[14]
                    if url.count("gif")>0 or url.count("jpg")>0 or url.count("jpeg")>0 or url.count("mp4")>0 or url.count("mov")>0 or url.count("mp3")>0 or url.count("swf")>0 \
                        or url.count("GIF")>0 or url.count("JPG")>0 or url.count("JPEG")>0 or url.count("MP4")>0 or url.count("MOV")>0 or url.count("MP3")>0 or url.count("SWF")>0 \
                        or url.count("exe")>0:
                        isSupported = True
                        if self.max_size<responseLen:
                            self.max_size = responseLen
                        size_sum = size_sum + responseLen
                        supported = supported + 1
                    else:
                        isSupported = False
                    try:
                        tmp = self.URLs_dict[url]['requested_num']
                        self.URLs_dict[url]['requested_num']=tmp+1
                        #print ('url exists')
                    except KeyError:
                        self.URLs_dict[url] = {'requested_num':1,'responseLen':responseLen,\
                                            'serverIP':fields[4].split(":")[0],'isSupported':isSupported}
                  
                    self.contents[url].append({'responseTime':responseTime,\
                    'DL_speed':responseLen/float(responseTime),'clientIP':fields[3].split(":")[0]})
                                            
                   
            line = f.readline()
        self.avg_size = size_sum/float(supported)
        f.close()
        print ('sorting...')
        #sort URLs based on number of times it is requested
        self.URLs_list = [u for (u,v) in sorted(self.URLs_dict.items(), key=lambda item: item[1], reverse=True)]
        #print (self.URLs_list)
        #print ('definelientIP')
        #self.defineClientsIP(self.logNum,self.aliveProb)
        n_contents = len(self.URLs_list)
        print (n_contents)
        self.zipf = TruncatedZipfDist(self.alpha, n_contents)
        duration = 50000000000#1/float(self.bigLambda*self.zipf.pdf[n_contents-1]);
        num_req =  int(self.bigLambda * duration);
        print ('generating traffic with size ' + str(num_req)+ ' ...')
        timestamp = 0
        #print ('clientIP: ' + c + ', number of req: ' + str(num_req_for_client),file=sys.stdout)

        outputPath = './output/' +  'dynamic_'+str(self.aliveProb) + '_' + self.cache_policy+'/'
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        fevents = open(outputPath+'events.txt','w')
        ###save contents#, clients and servers IPs
        print('zipf',file=fevents)
        print(str(self.alpha)+' ' +str(self.bigLambda),file=fevents)
        print(str(len(self.URLs_list)),file=fevents)    #contents number
        print(str(self.max_size),file=fevents)    #
        print(str(self.avg_size),file=fevents)    #            
        print(str(len(self.clientsIP)),file=fevents)        
        for c in self.clientsIP:
            print(c,file=fevents)
        print(str(len(self.serversIP)),file=fevents)        
        for s in self.serversIP:
            print(s,file=fevents)
        print(str(num_req),file=fevents)  
        client_server_speed = defaultdict(dict)   
        clientIP_list = list(self.clientsIP)
        for i in range(num_req):
            content = int(self.zipf.rv())
            url = self.URLs_list[content-1]
            #print (str(content) + ":" + url,file=sys.stdout)
            timestamp = int(timestamp + round((1/self.bigLambda) * abs(math.log10(random.random()))))
            clientIP = clientIP_list[random.randint(0,len(self.clientsIP)-1)]
            serverIP = self.URLs_dict[url]['serverIP']
            if clientIP in client_server_speed.keys():
                if serverIP in client_server_speed[clientIP].keys():
                    speed = client_server_speed[clientIP][serverIP]
            else:
                speed = random.randint(0,10)
                client_server_speed.setdefault(clientIP,{'serverIP': speed})
            
                       
            print (str(timestamp) + ' ' + url + ' ' + str(0) + \
            ' '+ str(speed) + ' ' + clientIP + ' ' + self.URLs_dict[url]['serverIP'] + ' '\
            + str(self.URLs_dict[url]['responseLen']) + ' ' + str(self.URLs_dict[url]['isSupported']),file=fevents)
                
#                self.eventList.append({'timestamp':int(timestamp),'URL':url, \
#                'responseTime':content_feature['responseTime'],\
#                'DL_speed':content_feature['DL_speed'],\
#                'clientIP':content_feature['clientIP'],\
#                'serverIP':self.URLs_dict[url]['serverIP'],\
#                'responseLen':self.URLs_dict[url]['responseLen'],\
#                'isSupported':self.URLs_dict[url]['isSupported']})
                    
        fevents.close()
     
        
    def generate_tracedriven_traffic(self,alpha):
        print ("read log files",file=sys.stdout)
        outputPath = './output/' +  'dynamic_'+str(self.aliveProb) + '_' + self.cache_policy+'/'
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        if os.path.exists(outputPath+'events.txt'):
            return
        ftemp = open(outputPath+'events_tmp.txt','w')    
        size_sum = 0
        supported = 0
        num_req = 0
        total_num_req = 0
        timestamp = 0
        urls = set()
        self.bigLambda = alpha
        for filename in os.listdir(self.logFile):
            self.eventList = []
            f = open(filename + '/' + self.logFile)
            ## Read the first line 
            line = f.readline()
            while line:
                #fields = [req_time,firstByteTime,LastByteTime,clientIP,ServerIP,clientHeader,
                #ServerHeader,IfModefinedSinceClientHeader,ExpiresServerHeader, LastModefiedServerHeader,responseHeaderLen,
                #responseDataLan,URLLen, GET, URLValue, HTTP/1.0]
                fields = line.split(" ")
                #if the request is not GET request deny it
             
                if fields[13]=='GET':
                    #compute response time in microseconds

                    responseLen = (int(fields[11])+int(fields[10]))
                    if responseLen<500000:
                        responseLen = responseLen * 800
                    elif responseLen<1000000:
                        responseLen = responseLen * 80
                    else:
                        responseLen = responseLen * 8
                    if responseLen>0:
                        start_dt = self.str2timestamp(fields[0])
                        end_dt = self.str2timestamp(fields[2])
                        responseTime = end_dt - start_dt
                        cip = fields[3].split(":")[0]
                        sip = fields[4].split(":")[0]
                        timestamp = self.str2timestamp(fields[0])
                        self.clientsIP.add(cip)
                        self.serversIP.add(sip)
                        url = fields[14]
                        urls.add(url)
                        if url.count("gif")>0 or url.count("jpg")>0 or url.count("jpeg")>0 or url.count("mp4")>0 or url.count("mov")>0 or url.count("mp3")>0 or url.count("swf")>0 \
                            or url.count("GIF")>0 or url.count("JPG")>0 or url.count("JPEG")>0 or url.count("MP4")>0 or url.count("MOV")>0 or url.count("MP3")>0 or url.count("SWF")>0 \
                            or url.count("exe")>0:
                            isSupported = True
                            if self.max_size<responseLen:
                                self.max_size = responseLen
                            size_sum = size_sum + responseLen
                            supported = supported + 1
                        else:
                            isSupported = False
                            
                        self.eventList.append({'URL':url,'timestamp':timestamp,'latency':responseTime,\
                                'speed':responseLen/float(responseTime),'clientIP':cip,'serverIP':sip,\
                                'len':responseLen,'isSupported':isSupported})
                    
                line = f.readline()
            #sort eventList on request timestamp
            self.eventList.sort(key=self.getKey)  
            num_req = len(self.eventList)
            total_num_req = total_num_req + num_req
            for e in self.eventList:
                timestamp = int(timestamp + round((1/self.bigLambda) * abs(math.log10(random.random()))))
                print( str(timestamp) + ' ' + e['URL'] + ' '+ str(e['latency']) + ' ' +\
                        str(e['speed']) + ' ' + e['clientIP'] + ' ' + e['serverIP'] + ' ' +\
                            str(e['len']) + ' ' + str(e['isSupported']),file=ftemp)
                            
            f.close()
        #end of for
        ftemp.close()           
        self.avg_size = size_sum/float(supported)
        fevents = open(outputPath+'events.txt','w')  
        print('trace_driven',file=fevents)
        print(str(self.bigLambda),file=fevents)
        print(str(len(urls)),file=fevents)    #contents number
        print(str(self.max_size),file=fevents)    #
        print(str(self.avg_size),file=fevents)    #            
        print(str(len(self.clientsIP)),file=fevents)        
        for c in self.clientsIP:
            print(c,file=fevents)
        print(str(len(self.serversIP)),file=fevents)        
        for s in self.serversIP:
            print(s,file=fevents)
        print(str(total_num_req),file=fevents) 
        print (total_num_req)
        ftemp = open(outputPath+'events_tmp.txt','r')
        line = ftemp.readline()
        while (line):
            print(line,file=fevents)
            line = ftemp.readline()
        ftemp.close()
        os.remove(outputPath+'events_tmp.txt')
        fevents.close()
              
        
        
    def printInfo(self):
        outputPath = './output/' +  'dynamic_'+str(self.aliveProb) + '_' + self.cache_policy+'/'
        f = open(outputPath+'info.txt','w')
        print ('*******PICN Simulation********', file=f)
        
        print ('Topology and traffic information:\n(client_seeker_BW:'+str(self.topology.bw_client_seeker)+' Mb/s)',file=f)
        print ('(seeker_seeker_BW:'+str(self.topology.bw_seeker_seeker)+' Mb/s)',file=f)
        print ('(local_p2p_uploadBW layer 1:'+str(self.topology.bw_p2p_upload_layer1)+' Mb/s)',file=f)
        print ('(local_p2p_uploadBW layer 2:'+str(self.topology.bw_p2p_upload_layer2)+' Mb/s)',file=f)
        print ('(remote_p2p_uploadBW:'+ str(self.topology.bw_p2p_remote_upload)+' Mb/s)',file=f)
        print ('(pserver_clinet_uploadBW:'+str(self.topology.bw_client_pserver)+' Mb/s) ',file=f)
        print ('(pserver_uploadBW:'+str(self.topology.bw_pserver_upload)+' Mb/s) ',file=f)
        #print ('(pserver_downloadBW:'+str(self.topology.bw_pserver_download)+ ' Mb/s)',file=f)
        print ('(peers_cache_size:'+str(self.topology.host_MaxCacheSize/float(8000000))+' MB)',file=f)
        print ('(pservers_cache_size:'+str(self.topology.pserver_MaxCacheSize/float(8000000))+' MB)\n',file=f)
        
        print (self.traffic_type,file=f)        
        print ('alpha value for zipf: ' + str(self.alpha),file=f)        
        print ('Total request rate: ' + str(self.bigLambda), file=f)
        print ('request rate for each client: ' + str(self.bigLambda/float(len(self.clientsIP))),file=f)
        print ('Total number of requests:' + str(self.eventNum),file=f)
        print ('Total number of clients:' + str(len(self.clientsIP)),file=f)
        print ('Number of LANs:' + str(len(self.topology.seeker_nodes)),file=f)
        print ('number of webservers:' + str(len(self.serversIP)),file=f)
        print ('number of different URLs:' + str(self.URLsNum),file=f)
        print ('maximum size of contents: ' + str(self.max_size),file=f)
        print ('average size of contents: ' + str(self.avg_size) +'\n',file=f)
        
        f.close()
        
    def loadEvents(self):
        outputPath = './output/' +  'dynamic_'+str(self.aliveProb) + '_' + self.cache_policy+'/'
        fevents = open(outputPath+'events.txt')
        line = fevents.readline()
        self.traffic_type = line
        print (line.rstrip())
        if (line.rstrip()=='zipf'):
            line = fevents.readline().rstrip()
            self.alpha = float(line.split(' ')[0])
            self.bigLambda = float(line.split(' ')[1])
        else:
            line = fevents.readline().rstrip()	
        self.bigLambda = float(line)
        line = fevents.readline()
        self.URLsNum = int(line)
        line = fevents.readline()
        self.max_size = int(line)
        line = fevents.readline()
        self.avg_size = float(line)
        line = fevents.readline()       #number of clients
        for i in range(int(line)):
            line = fevents.readline()
            self.clientsIP.add(line.rstrip())
        line = fevents.readline()       #number of servers
        for i in range(int(line)):
            line = fevents.readline()
            self.serversIP.add(line.rstrip())    
        self.eventNum = int (fevents.readline())    
        self.eventFilePos = fevents.tell()
        self.defineClientsIP()
        fevents.close()
        
        
        
if __name__=='__main__':
    parser = OptionParser()
   
    parser.add_option("-p", "--path", dest="traceFiles_path",
                      help="Path to trace files for generating request traffic")
    parser.add_option("-c", "--cache_policy", dest="cpolicy",
                      help="caching policy (fully_redundant, no_redundant, popularity_based)")
    parser.add_option("-r", "--rate", dest="reqRate",
                      help="request rate")
    parser.add_option("-a", "--availability", dest="availability",
                      help="probability of client availability")
    
    (options, args) = parser.parse_args()
    availability = (float(options.availability)) if options.availability else 100
    traceFile_path = (options.traceFiles_path) if options.traceFiles_path else './trace_detail_1'
    reqRate = (float(options.reqRate)) if options.reqRate else 0.0005
    policy = (options.cpolicy) if options.cpolicy else 'full_redundant'
    
    simulator = SimulatorGenerator(traceFile_path,availability,policy)
        
    #simulator = SimulatorGenerator('/home/zali/Simulation/UC_Berkeley/tools/trace_detail_',\
    #                              logNum, 100)
    #simulator.generate_zipf_traffic(0.8,0.0001)
    simulator.generate_tracedriven_traffic(reqRate)
    #nx.draw(e.topology.topologyGraph)

