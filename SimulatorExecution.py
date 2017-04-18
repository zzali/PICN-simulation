# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 12:34:32 2016

@author: Zeinab Zali
"""


from __future__ import print_function
from Request import Request
from SimulatorGenerator import SimulatorGenerator
import sys
from optparse import OptionParser

class SimulatorExecution(object):
   
    def __init__(self,logFile, dataset, aliveProb, cachePolicy,cache_size,trace_day=None): 
        if dataset=='Berkeley':
            self.simulator = SimulatorGenerator(dataset, logFile , cache_size, aliveProb, cachePolicy)
            self.simulator.loadEvents(True)                                       
            self.simulator.printInfo(True)
            self.supported = 0
        else:
            self.simulator = SimulatorGenerator(dataset, logFile , cache_size, aliveProb, cachePolicy, day=trace_day)
            self.simulator.loadEvents(True)                                       
            self.simulator.printInfo(True)
            self.supported = 0
        
    
    def execute(self,proxy):
#        URLs = set()
        enum = 1
        eventList = self.simulator.nextEventList()
        
        while (eventList is not None):
            for event in eventList:
                print('req '+str(enum),file=sys.stdout)
                req = Request(enum, event['timestamp'], event['responseTime'], event['clientIP'], event['serverIP'], event['URL'], \
                              event['responseLen'], event['RTT'], event['BW'], event['proxy_provider'] )
                
                req = self.simulator.topology.compute_purewebTime(req)
                if event['isSupported']:
                    if proxy and req.latency>0:
                        self.simulator.topology.compute_proxy_time(req)
                        
                    self.simulator.topology.seek(req)
                 
                enum = enum + 1
            eventList = self.simulator.nextEventList()
        self.simulator.topology.results.dumpAllFiles(proxy)
        self.simulator.topology.results.draw(proxy)
        self.simulator.topology.f.close()
        self.simulator.topology.fpop.close()
        
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
    parser.add_option("-D", "--Dataset", dest="dataset",
                      help="dataset (IRCache,Berkeley)")     
    parser.add_option("-d", "--day", dest="day",
                      help="Trace day (9,10)")     
    parser.add_option("-m", "--cache_size", dest="cache_size",
                      help="Host cache storage size (KB)")   
    
    (options, args) = parser.parse_args()
    availability = (float(options.availability)) if options.availability else 100
    traceFile_path = (options.traceFiles_path) if options.traceFiles_path else './Data'
    policy = (options.cpolicy) if options.cpolicy else 'fully_redundant'
    trace_day = (options.day) if options.day else '9'
    cache_size = int(options.cache_size)*1000 if options.cache_size else 1000000000#Bytes
    dataset = (options.dataset) if options.dataset else 'IRCache'
    if options.proxy:
        if options.proxy=='yes':
            proxy = True 
        else:
            proxy = False
    else:
        proxy==False
                      
    simulatorexe = SimulatorExecution(traceFile_path, dataset, availability,policy, cache_size, 
                                      trace_day=trace_day)
    simulatorexe.execute(proxy)
    
                                            
    
