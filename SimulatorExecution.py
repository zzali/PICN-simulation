# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 12:34:32 2016

@author: Zeinab Zali
"""


from __future__ import print_function
from Request import Request
from SimulatorGenerator import SimulatorGenerator
import os
import sys
from optparse import OptionParser

class SimulatorExecution(object):
   
    def __init__(self,logFile, aliveProb, cachePolicy):
        self.simulator = SimulatorGenerator(logFile , aliveProb, cachePolicy)
        self.simulator.generate_tracedriven_traffic(reqRate)
        #self.simulator = SimulatorGenerator('/home/nasr/CCN/tools/trace_detail_'+ logNum,\
        #                                        logNum,aliveProb,1)
        self.simulator.loadEvents()                                       
        self.simulator.printInfo()
        self.supported = 0
        
    
    #bw<2.5, delay>9ms
    def estimate_bw_delay_from_ws(self,DL_speed):
        if DL_speed<0.001:
            return [0.5,100000]
        if DL_speed<0.002:
            return [1,100000]
        if DL_speed<0.004:
            return [1.5,80000]
        if DL_speed<0.006:
            return [2,80000]
        if DL_speed<0.008:
            return [2.5,70000]
        if DL_speed<0.01:
            return [3,60000]
        if DL_speed<0.02:
            return [4,50000]
        if DL_speed<0.04:
            return [5,40000]
        if DL_speed<0.06:
            return [6,30000]
        if DL_speed<0.08:
            return [7,20000]
        return [10,10000]

#    def estimate_bw_delay_from_ws(self,DL_speed):
#        if DL_speed==0:
#            return [0.5,100000]
#        if DL_speed==1:
#            return [1,100000]
#        if DL_speed==2:
#            return [1.5,80000]
#        if DL_speed==3:
#            return [2,80000]
#        if DL_speed==4:
#            return [2.5,70000]
#        if DL_speed==5:
#            return [3,60000]
#        if DL_speed==6:
#            return [4,50000]
#        if DL_speed==7:
#            return [5,40000]
#        if DL_speed==8:
#            return [6,30000]
#        if DL_speed==9:
#            return [7,20000]
#        return [10,10000]   

    def execute(self):
        URLs = set()
        enum = 1
        #event = self.simulator.nextEevent()
        eventList = self.simulator.nextEventList()
        #while (event is not None):
        while (eventList is not None):
            for event in eventList:
                print(enum,file=sys.stdout)
                
                bw_delay = self.estimate_bw_delay_from_ws(event['DL_speed'])
     
                req = Request(enum,event['clientIP'], event['URL'], event['timestamp'], event['responseLen'])
                            
                estimatedResponseTime = event['responseLen']/float(bw_delay[0]) + bw_delay[1]
                
                if event['isSupported']:
                    #print('size= '+ str(event['responseLen']/(1000)),file=sys.stdout)
                    self.simulator.topology.compuet_CDN_time(req,bw_delay[0],bw_delay[1]);
                    URLs.add(event['URL'])
                    self.supported = self.supported + 1
                    self.simulator.topology.seek(req, bw_delay,estimatedResponseTime)        
                #else:
                    #self.simulator.topology.register(event['clientIP'], event['URL'], event['responseLen'],event['timestamp']+estimatedResponseTime)
                    #self.simulator.topology.results.add_webDL(req.URL,req.responseLen,estimatedResponseTime)
                    #self.simulator.topology.register_in_local_host(-1, event['URL'], event['responseLen'], event['timestamp'],event['clientIP'])
                    #self.simulator.topology.results.add_webDL(req.URL,req.responseLen,estimatedResponseTime)
                enum = enum + 1
            eventList = self.simulator.nextEventList()
            #event = self.simulator.nextEevent()
        self.simulator.topology.results.dumpAllFiles()
        self.simulator.topology.results.draw()
        self.simulator.topology.f.close()
        
if __name__=='__main__':
    logNum = str('')
    #aliveProb = 100
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
                      
    simulatorexe = SimulatorExecution(traceFile_path, availability,policy)
    simulatorexe.execute()
    outputPath = './output/' + 'dynamic_'+str(availability) + '_' + policy+'/'
    
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
        
    f = open(outputPath + 'info.txt','a')
    print('number of denied remote peer Download: ' + str(simulatorexe.simulator.topology.deniedPeerDL)+', '+\
                                                        str(simulatorexe.simulator.topology.deniedPeerDL/float(simulatorexe.supported))\
                                                        ,file=f)
    print ('number of supported PICN requests: ' + str(simulatorexe.supported),file=f)
    print ('number of unsupported PICN requests: ' + str(len(simulatorexe.simulator.eventList)-simulatorexe.supported)+'\n',file=f)
    
    
    hitRatio = (simulatorexe.simulator.topology.local_foundnum + simulatorexe.simulator.topology.localPeer_foundnum + \
            simulatorexe.simulator.topology.remotePeer_foundnum)/float(simulatorexe.supported)
    
    print ('Total Hit ratio in PICN (local cache + local peers + remote peers): ' + str(hitRatio),file=f)
    print ('Hit ratio in local cache in PICN: ' + str(simulatorexe.simulator.topology.local_foundnum/float(simulatorexe.supported)),file=f)

    print ('Hit ratio in local peer in PICN: ' + str(simulatorexe.simulator.topology.localPeer_foundnum/float(simulatorexe.supported)),file=f)

    print ('Hit ratio in remote peer in PICN: ' + str(simulatorexe.simulator.topology.remotePeer_foundnum/float(simulatorexe.supported)),file=f)
   
    print ('Miss ratio in caches in PICN: ' + str(simulatorexe.simulator.topology.notFoundnum/float(simulatorexe.supported)),file=f)
    #tot = simulatorexe.simulator.topology.CDN_miss + simulatorexe.simulator.topology.CDN_Hit
    print ('\n',file=f)
    hitRatio = (simulatorexe.simulator.topology.CDN_Hit + simulatorexe.simulator.topology.local_foundnum_CDN)/float(simulatorexe.supported)
            
    print ('Total Hit ratio with proxy servers (proxy servers+local cache): '+ str(hitRatio),file=f)
    print ('Miss ratio in proxy servers: ' + str(simulatorexe.simulator.topology.results.CDN_miss/float(simulatorexe.supported)),file=f)
    print ('Hit ratio in proxy servers: ' + str(simulatorexe.simulator.topology.CDN_Hit/float(simulatorexe.supported)),file=f)
    print ('Hit ratio in local cache of hosts connected to proxy servers: ' + str(simulatorexe.simulator.topology.local_foundnum_CDN/float(simulatorexe.supported)),file=f)
    f.close()

    #simulatorexe.simulator.topology.results.draw(outputPath)
                                            
    
