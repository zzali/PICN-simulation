# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 09:09:19 2017

@author: root
"""



from __future__ import print_function
from Request import Request
from SimulatorGenerator import SimulatorGenerator
import sys
from optparse import OptionParser
from RequestProvider import RequestProvider

class SimulatorExecution(object):

    def __init__(self,logFile, dataset, aliveProb, cachePolicy,cache_size,trace_day=None,rate=None): 
        if dataset=='Berkeley':
            self.simulator = SimulatorGenerator(dataset, logFile , cache_size, aliveProb, cachePolicy, rate=rate)
            self.simulator.loadEvents(False)                                       
            self.simulator.printInfo(False)
            self.supported = 0
        else:
            self.simulator = SimulatorGenerator(dataset, logFile , cache_size, aliveProb, cachePolicy, rate=rate, day=trace_day)
            self.simulator.loadEvents(False)                                       
            self.simulator.printInfo(False)
            self.supported = 0  
        clientsIP = self.simulator.readClientsIP()  
        self.reqProvider = RequestProvider(dataset,clientsIP,aliveProb, 3, cachePolicy,cache_size)
        self.aliveProb = aliveProb
        self.trace_day = trace_day
        self.cachePolicy = cachePolicy
        self.cache_size = cache_size

    
    def execute(self,proxy):
#        URLs = set()
        enum = 1
        eventList = self.simulator.nextEventList()
        proxy_hit = 0
        proxy_miss = 0
        tot_traffic = 0
        if dataset=='Berkeley':
            self.outputPath = './output/'+dataset+'/dynamic'+ str(self.aliveProb) + '_' + \
                self.cachePolicy + '_cacheSize'+ str(cache_size/1000000) +'MB' + '/'
        else:
            self.outputPath = './output/'+dataset+'/dynamic'+ str(self.aliveProb) + '_' + \
            self.cachePolicy + '_cacheSize'+ str(cache_size/1000000) +'MB' + '/'+ self.trace_day + '/'
            
        f = open(self.outputPath+'info_noLatency.txt','a')
        while (eventList is not None):
            for event in eventList:
                print('req '+str(enum),file=sys.stdout)
               
                req = Request(enum, event['timestamp'], event['responseTime'], event['clientIP'], event['serverIP'], event['URL'], \
                              event['responseLen'], event['RTT'], event['BW'], event['proxy_provider'] )
                
                if event['isSupported']:
                    tot_traffic += event['responseLen']
                    if event['responseLen'] > 1000000000:
                        print(event,file=f) 
                    if proxy and req.latency>0:
                        if event['proxy_provider'].count('HIT')>0:
                            proxy_hit += 1
                        elif event['proxy_provider'].count('MISS')>0:
                            proxy_miss += 1
                    self.reqProvider.seek(req)
                    self.supported += 1
#                
                enum = enum + 1
            eventList = self.simulator.nextEventList()
            #event = self.simulator.nextEevent()
  
        print('\n',file=f)
     
        print('tot traffic: ',tot_traffic)
        print('total traffic: '+str(tot_traffic),file=f)
        print('number of supported requests: '+str(self.supported),file=f)
        print('\n',file=f)
        print('proxy hit ratio: '+ str(round(proxy_hit/float(self.supported)*100,3)),file=f)
        print('proxy miss ratio: '+ str(round(proxy_miss/float(self.supported)*100,3)),file=f)
        print('\n',file = f)
        print('local cache hit ratio: '+ str(round(self.reqProvider.local_hit/float(self.supported)*100,3)),file=f)
        print('p2p hit ratio: '+str(round(self.reqProvider.p2p_hit/float(self.supported)*100,3)),file=f)
        print('remote p2p hit ratio: '+str(round(self.reqProvider.rp2p_hit/float(self.supported)*100,8)),file=f)
        print('Total hit ratio: '+str(round((self.reqProvider.rp2p_hit+self.reqProvider.p2p_hit+self.reqProvider.local_hit)/float(self.supported)*100,3)),file=f)
        print('picn miss ratio: '+str(round(self.reqProvider.miss/float(self.supported)*100,3)),file=f)
        print('saved traffic from local cache hit ratio: '+ str(round(self.reqProvider.local_hit_size/float(tot_traffic)*100,3)),file=f)
        print('saved traffic from p2p hit ratio: '+str(round(self.reqProvider.p2p_hit_size/float(tot_traffic)*100,3)),file=f)
        print('saved traffic from remote p2p hit ratio: '+str(round(self.reqProvider.rp2p_hit_size/float(tot_traffic)*100,8)),file=f)
        print('saved traffic from Total hit ratio: '+str(round((self.reqProvider.rp2p_hit_size+self.reqProvider.p2p_hit_size+self.reqProvider.local_hit_size)/float(tot_traffic)*100,3)),file=f)
        print('picn miss traffic ratio: '+str(round(self.reqProvider.miss_size/float(tot_traffic)*100,3)),file=f)
        f.close()
        
if __name__=='__main__':
    logNum = str('')
    #aliveProb = 100
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="traceFiles_path",
                      help="Path to trace files for generating request traffic")
    parser.add_option("-c", "--cache_policy", dest="cpolicy",
                      help="caching policy (fully_redundant, no_redundant, popularity_based)")
    parser.add_option("-a", "--availability", dest="availability",
                      help="probability of client availability")
    parser.add_option("-s", "--proxyserver", dest="proxy",
                      help="whether compare with proxy or not (yes,no)")
    parser.add_option("-r", "--rate", dest="reqRate",
                      help="request rate factor (1,2,3,...)")
    parser.add_option("-D", "--Dataset", dest="dataset",
                      help="dataset (IRCache,Berkeley)")     
    parser.add_option("-d", "--day", dest="day",
                      help="Trace day (9,10)")     
    parser.add_option("-m", "--cache_size", dest="cache_size",
                      help="Host cache storage size (KB)")   
    
    (options, args) = parser.parse_args()
    availability = (float(options.availability)) if options.availability else 100
    traceFile_path = (options.traceFiles_path) if options.traceFiles_path else './Data'
    reqRate = (int(options.reqRate)) if options.reqRate else 1
    policy = (options.cpolicy) if options.cpolicy else 'fully_redundant'
    trace_day = (options.day) if options.day else '9'
    cache_size = int(options.cache_size)*1000 if options.cache_size else 1000000000#Bytes
    rate = int(options.reqRate) if options.reqRate else 1
    dataset = (options.dataset) if options.dataset else 'IRCache'
    if options.proxy:
        if options.proxy=='yes':
            proxy = True 
        else:
            proxy = False
    else:
        proxy==False
                      
    simulatorexe = SimulatorExecution(traceFile_path, dataset, availability,policy, cache_size, 
                                      trace_day=trace_day, rate = rate)
    simulatorexe.execute(proxy)
                                            
    
