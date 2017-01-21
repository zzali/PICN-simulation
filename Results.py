# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 11:45:13 2016

@author: Zeinab Zali
"""
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib import font_manager
from optparse import OptionParser


class Results(object):
    def __init__(self, out_path):
        self.memBuffSize = 10000
        self.reqList = [] #[URL,responseLen,responseTime,DL_speed,[localPeer=0,remorePeer=1,mainwebserver=2]]
        self.reqList_CDN = [] #[URL,responseLen,responseTime,DL_speed,Hit]
        self.p2p_url_speed = defaultdict(list)
        self.p2p_url_remote_speed = defaultdict(list)
        self.web_url_speed = defaultdict(list)
        
        self.p2p_size_time = defaultdict(list)
        self.p2p_remote_size_time = defaultdict(list)
        self.web_size_time = defaultdict(list)
        self.pureweb_size_time = defaultdict(list)
        self.CDN_hit_size_time = defaultdict(list)
        self.CDN_miss_size_time = defaultdict(list)
        
        
        self.p2p_speed = []
        self.p2p_remote_speed = []
        self.web_speed = []
        self.PICN_speed = []
        
        self.size_avgTime_localpeer = []
        self.size_avgTime_remotepeer = []
        self.size_avgTime_web = []
        self.size_avgTime_pureweb = []
        
        self.p2p_list = []
        self.p2p_remote_list = []
        self.web_list = []
        self.local_list = []
        self.local_CDN_list = []
        self.Hit_pserver_list = []
        self.Miss_pserver_list = []
        self.url_set = set()
        self.speed_url_web = {}
        self.CDN_reqID_times = {}
        
        self.CDN_miss = 0
        self.hitCDN_speed = []
        self.missCDN_speed = []
        self.speed_url_missCDN = defaultdict(list)
        self.size_avgSpeed_hitCDN = []
        self.out_path = out_path
        self.reqID_static = 7600
        
                    
        
        
    def add_Hit(self,reqID,URL,responseLen,responseTime):
        #print ('hit in CDN')
        #print("add Hit",file=sys.stdout)
        speed = responseLen/float(responseTime)
        #self.hitCDN_speed.append(speed)
        #if (responseLen>125000):
        self.reqList_CDN.append({'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'hit':True,'overhead':0})       
       # if (reqID==self.reqID_static):
       # print('cdn hit: '+ str(reqID) + ':' + str(speed))
        #self.CDN_hit_size_time[str(responseLen)].append([responseTime,0])
        if (len(self.reqList_CDN)>self.memBuffSize):
            CDN_hit_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==True] 
            self.dumplist(self.out_path+'CDN_Hit',CDN_hit_list)
            
            CDN_miss_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==False] 
            self.dumplist(self.out_path+'CDN_Miss',CDN_miss_list)
            self.reqList_CDN = []
        
            
                            
    #if provider=0 it is downloaded to pserver else if = 1 it is downloaded to client
    def add_miss(self,reqID,URL,responseLen,responseTime,provider):
        #print("add miss",file=sys.stdout)  
        #print ('miss in CDN')
        speed = 0
        if self.CDN_reqID_times.has_key(reqID) :
            t = self.CDN_reqID_times.get(reqID)
            if t < responseTime:
                speed = responseLen/float(responseTime)
                self.CDN_reqID_times.update({reqID:responseTime})
                self.reqList_CDN.append({'URL':URL,'len':responseLen,'latency':responseTime,\
                        'speed':speed,'hit':False,'overhead':0})  
                self.CDN_miss = self.CDN_miss + 1
               #self.CDN_miss_size_time[str(responseLen)].append([responseTime,0])
            else:
                speed = responseLen/float(t)
                self.reqList_CDN.append({'URL':URL,'len':responseLen,'latency':t,\
                        'speed':speed,'hit':False,'overhead':0})  
                #self.CDN_miss_size_time[str(responseLen)].append([t,0])
            #self.speed_url_missCDN[URL].append(speed)
            #self.missCDN_speed.append(speed)
   #         if (reqID==self.reqID_static):
    #            print('cdn miss: '+str(speed),file=sys.stdout)
            return True
        else:
            self.CDN_reqID_times.update({reqID:responseTime})
      #      if (reqID==self.reqID_static):
       #         print('cdn miss: '+str(speed),file=sys.stdout)
            #self.CDN_miss_size_time[str(responseLen)].append([responseTime,0])
            return False
        if (len(self.reqList_CDN)>self.memBuffSize):
            CDN_hit_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==True] 
            self.dumplist(self.out_path+'CDN_Hit',CDN_hit_list)
            
            CDN_miss_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==False] 
            self.dumplist(self.out_path+'CDN_Miss',CDN_miss_list)
            self.reqList_CDN = []
    
    def add_localDL(self,reqID,URL,responseLen):
        self.url_set.add(URL)
        self.local_list.append({'URL':URL,'len':responseLen,'latency':0,\
                            'speed':0,'overhead':0})
        if(len(self.local_list)>self.memBuffSize):
            self.dumplist(self.out_path+'local_PICN',self.local_list)
    #    if reqID==self.reqID_static:
     #       print('local picn: ')
            
           
    def add_localDL_CDN(self,reqID,URL,responseLen):
        self.local_CDN_list.append({'URL':URL,'len':responseLen,'latency':0,\
                            'speed':0,'overhead':0})
  #      if reqID==self.reqID_static:
   #         print('local cdn: ' )
        #print ('find in local cache in CDN')
        if(len(self.local_CDN_list)>self.memBuffSize):
            self.dumplist(self.out_path+'local_CDN',self.local_CDN_list)   
                  
       
    def add_peerDL(self,reqID,URL,responseLen,responseTime,overhead,isLocalpeer):
        #print("add peerDL",file=sys.stdout)
        
        self.url_set.add(URL)
        speed = responseLen/float(responseTime)
        if isLocalpeer:
            provider = 0
#            self.p2p_url_speed[URL].append(speed)
#            self.p2p_size_time[str(responseLen)].append([responseTime,overhead])
#            self.p2p_speed.append(speed)
        else:
            provider = 1
#            self.p2p_url_remote_speed[URL].append(speed)
#            self.p2p_remote_size_time[str(responseLen)].append([responseTime,overhead])
#            self.p2p_remote_speed.append(speed)
        self.reqList.append({'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'provider':provider,'overhead':overhead})
        #if (responseLen>125000):
        self.PICN_speed.append(speed)
        #if reqID==self.reqID_static:
    #    print('peer hit: ' + str(reqID) + ':' + str(speed))
        if (len(self.reqList)>self.memBuffSize):
            p2p_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==0] 
            self.dumplist(self.out_path+'p2p_local_list',p2p_list)
            #
            p2p_remote_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==1] 
            self.dumplist(self.out_path+'p2p_remote_list',p2p_remote_list)
          
            web_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==2] 
            self.dumplist(self.out_path+'web_list',web_list)
            self.reqList = []
            
      
    def add_webDL(self,reqID, URL,responseLen,responseTime, overhead):
        
        self.url_set.add(URL)
        speed = responseLen/float(responseTime)        
        self.reqList.append({'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'provider':2,'overhead':overhead})
        if (len(self.reqList)>self.memBuffSize):
            p2p_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==0] 
            self.dumplist(self.out_path+'p2p_local_list',p2p_list)
            #
            p2p_remote_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==1] 
            self.dumplist(self.out_path+'p2p_remote_list',p2p_remote_list)
            web_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==2] 
            self.dumplist(self.out_path+'web_list',web_list)
            self.reqList = []
   #     if reqID==self.reqID_static:
    #        print('web speed:'+str(speed))
        #self.web_url_speed[URL].append(speed)
        #self.web_size_time[str(responseLen)].append([responseTime,overhead])
        #self.pureweb_size_time[str(responseLen)].append([responseTime-overhead,0])
        
        #self.web_speed.append(speed)
        #self.PICN_speed.append(speed)
            
        #if(responseLen/float(responseTime))>1:
         #   print self.reqList[len(self.reqList)-1]
        
    
    def calculate_url_speed(self,url_set, in_list):
        speed_url = {}        
        for url in url_set:
            sum = 0
            n = 0            
            for r in in_list[url]:
                #if r < 0 :
                #    print r
                sum = sum + r
                n = n + 1
            if n > 0:
                speed_url.update({url:sum/float(n)})
            else:
                speed_url.update({url:None})
        return speed_url
        
     
    def getKey(self,in_list):
        return in_list[0][0]
        
    #sort the dictionary in form {size,[[speed,overhead],..]} based on size 
    #and return it in a new list in form [[[size,size][speed,overhead],...[speed,overhead]],...,[[size,size][speed,overhead],...[speed,overhead]]]
    #avg_size
    def sortDict_2list(self,in_dict):
        #print 'call sortDict_2list'
        in_list = []
        avg_size = 0
        for a in in_dict.keys():
            #print a
            size = int(a)
            avg_size = avg_size + size
            newlist = []
            newlist.append([size,size])
            for k in in_dict[a]:
                newlist.append(k)
            in_list.append(newlist)              
        in_list.sort(key=self.getKey)
        #print in_list
        if len(in_list)>0:
            max_size = in_list[len(in_list)-1][0][0]
            avg_size = avg_size / float(len(in_list))
        #print 'max_size:' + str(max_size)
        else:
            max_size = 0
            avg_size = 0
        
        #print in_list[len(in_list)-1]
        return avg_size,max_size,in_list
        
    def sortDict(self,in_dict):
        sorted_dict = {}
        for key in sorted(in_dict.iterkeys()):
            sorted_dict.update({key:in_dict[key]})
        return sorted_dict
        
    def calculate_size_time(self,in_list,min_size, max_size):
        #print 'call calculate_size_time'
        size_time= defaultdict(list)
        size_list = []
        r = min_size / 10
        d = r / 10 
        for i in range(10):
            size_list.append(d*(i+1))
        end = d*10
        d = (min_size-r) / 10 
        for i in range(10):
            size_list.append(d*(i+1)+end)
        end = d*10+end
        d = (max_size-end)/ 5 
        for i in range(5):
            size_list.append(d*(i+1)+end)
        #print size_list
        i = 0
        sum_time = 0
        sum_overhead = 0
        n = 0
        #print size_list
        for length in size_list:
            while i<len(in_list) and in_list[i][0][0]<=length:
                #print l[0:]
                for time_overhead in in_list[i][1:]:
                    if time_overhead[0]>0:
                        sum_time = sum_time + time_overhead[0]
                        sum_overhead = sum_overhead + time_overhead[1]
                        n = n + 1
                i = i + 1
            #print length,': ', n                
            if n > 0:
                size_time[str(length)].append(sum_time/float(n))
                size_time[str(length)].append(sum_overhead/float(n))
            else:
                size_time[str(length)].append(0)
                size_time[str(length)].append(0)
            n = 0
            sum_time = 0
            sum_overhead = 0
        
        #print size_time,len(size_time)  
                
        return size_list, size_time
        
  
    def dumpdict(self,fname,dictkeys,dictvalues):
        with open(fname, 'w') as fout:
            for i in range(len(dictkeys)):
                fout.write( str(dictkeys[i])+ " : " + str(dictvalues[i]) +'\n')     
        fout.close() 
        
    def dumplist(self,fname,listname):
        with open(fname, 'a') as fout:
            while len(listname)>0:            
                r = listname.pop(0)
                print( r['URL'] + ' ' + str(r['speed']) + ' '+ str(r['len'])\
                + ' '+ str(r['latency'])+ ' '+ str(r['overhead']),file=fout)     
        fout.close() 
        
    def loadlist(self,fname):
        #print 'loading list '+fname
        fout = open(fname,'r')
        line = fout.readline()
        outList = []
        while (line):
            fields = line.split(' ')
            if len(fields)>=5:
                outList.append({'URL':fields[0],'speed':float(fields[1]),'len':int(fields[2]),\
                            'latency':float(fields[3]),'overhead':float(fields[4])})
            line = fout.readline()
        fout.close() 
        return outList
        
    def cdf(self,vector,max_speed):
        interval_num = 50
        cdf = []
        x = np.arange(0,max_speed,max_speed/interval_num)
        y = []
        y.append(0)
        for i in range(len(x)-1):
            y.append(len([speed for speed in vector if speed>x[i] and speed<=x[i+1]]))
        #print y
        #print 'sum:'
        #print np.sum(y)
        #print 'cumsum'
        #print np.cumsum(y)
        cdf = np.cumsum(y)/float(np.sum(y))
        #print max_speed
        return cdf, x
    
    def plot_cdf_speed_PICN(self):
        print ('plot cdf_speed_PICN...')  
        
        print('calculating cdf of p2p')
        listout = self.loadlist(self.out_path+'p2p_local_list')
        print('list is loaded from the file')
        p2p_speed_list = [r['speed'] for r in listout]
        listout = []
        max_speed = max(p2p_speed_list) 
        p2pNum = len(p2p_speed_list)
        print('cdf')
        
                
        print('calculating cdf of web')        
        listout = self.loadlist(self.out_path+'web_list')
        web_speed_list = [r['speed'] for r in listout]
        listout = []
        max_speed = max([max_speed,max(web_speed_list)])
        p2p_cdf,p2p_speed = self.cdf(p2p_speed_list,max_speed)
        p2p_speed_list = []          
        webNum = len (web_speed_list)
        web_cdf,web_speed = self.cdf(web_speed_list,max_speed)
        web_speed_list = []
       
        print('calculating cdf of p2p_remote')
        listout = self.loadlist(self.out_path+'p2p_remote_list')
        p2p_remote_speed_list = [r['speed'] for r in listout]
        listout = []
        p2p_remoteNum = len(p2p_remote_speed_list)
        p2p_remote_cdf,p2p_remote_speed = self.cdf(p2p_remote_speed_list,max_speed)
        p2p_remote_speed_list = []       
        
        listout = self.loadlist(self.out_path+'local_PICN')
        localNum = len(listout)
        listout = []
        f = open(self.out_path + 'info.txt','a')
        tot = p2pNum + p2p_remoteNum + webNum + localNum
        print ('Total number of supportes requests: ' + str(tot),file=f)
        print ('Hit ratio in local cache in PICN:' + str(localNum/float(tot)),file=f)
        print ('Hit ratio in local peer in PICN: ' + str(p2pNum/float(tot)),file=f)
        print ('Hit ratio in remote peer in PICN: ' + str(p2p_remoteNum/float(tot)),file=f)
        f.close()
        #print 'plotting speed cdf...'
        plt.ion()
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)    
        diag_p2p = ax.plot(p2p_speed,p2p_cdf,color='g',linestyle='--',marker='',linewidth = 3,label='Local peers (via PICN)')
        diag_p2p_remote = ax.plot(p2p_remote_speed,p2p_remote_cdf,color='b',linestyle='-.',marker='',linewidth = 3,label='Remote peers (via PICN)')
        diag_web = ax.plot(web_speed,web_cdf,color='k',marker='',linestyle=':',linewidth = 3,label='webserver')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_p2p[0],diag_p2p_remote[0],diag_web[0]),('Local peers (via PICN)','Remote peers (via PICN)','Original web server'),loc=0,fontsize=18) 
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'PICN_CDF.pdf',format='PDF',dpi=5)
        #plt.show(fig,block=False)
        #plt.close(fig)
        
    
    def plot_cdf_speed_CDN(self):
        print ('plot cdf_speed_CDN...')
                
        listout = self.loadlist(self.out_path+'CDN_Hit')
        cdn_hit_num = len(listout)
        CDN_Hit_speed_list = [r['speed'] for r in listout]
        listout = []
        max_speed = max(CDN_Hit_speed_list)
                      
        
        listout = self.loadlist(self.out_path+'CDN_Miss')
        cdn_miss_num = len (listout)
        CDN_Miss_speed_list = [r['speed'] for r in listout]
        listout = []
        max_speed = max([max_speed,max(CDN_Miss_speed_list)])
        Hit_cdf,Hit_speed = self.cdf(CDN_Hit_speed_list,max_speed)
        CDN_Hit_speed_list = []
        Miss_cdf,Miss_speed = self.cdf(CDN_Miss_speed_list,max_speed)
        CDN_Miss_speed_list = []        
        
        listout = self.loadlist(self.out_path+'local_CDN')
        localNum = len(listout)
        listout = []
        f = open(self.out_path + 'info.txt','a')
        tot = cdn_hit_num + cdn_miss_num + localNum
        print ('Hit ratio in local cache in CDN:' + str(localNum/float(tot)),file=f)
        print ('Hit ratio in proxy server in CDN: ' + str(cdn_hit_num/float(tot)),file=f)
        print ('Miss ratio in proxy server in CDN: ' + str(cdn_miss_num/float(tot)),file=f)
        f.close()
        #print 'plotting speed cdf...'
        plt.ion()
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        diag_Hit = ax.plot(Hit_speed,Hit_cdf,color='r',linestyle='-',marker='x',linewidth = 3,label='proxy servers')
        diag_Miss = ax.plot(Miss_speed,Miss_cdf,color='k',linestyle=':',linewidth = 3,label='Original web server')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_Hit[0],diag_Miss[0]),('proxy servers','Original web server'),loc=0,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'CDN_CDF.pdf',format='PDF',dpi=5)
        #plt.show(fig,block=False)
        #plt.close(fig)
        
    def plot_cdf_PICNPeers_CDNHit(self):
        print ('plot cdf_PICNpeers_CDNHit...')
        listout = self.loadlist(self.out_path+'CDN_Hit')
        CDN_Hit_speed_list = [r['speed'] for r in listout]
        listout = []
        max_speed = max(CDN_Hit_speed_list)
                
        listout = self.loadlist(self.out_path+'p2p_local_list')
        PICN_speed_list = [r['speed'] for r in listout]
        listout = []        
        listout = self.loadlist(self.out_path+'p2p_remote_list')
        for r in listout:
            PICN_speed_list.append(r['speed'])
        max_speed = max([max_speed,max(PICN_speed_list)])
        Hit_cdf,Hit_speed = self.cdf(CDN_Hit_speed_list,max_speed)
        CDN_Hit_speed_list = []        
        PICN_cdf,PICN_speed = self.cdf(PICN_speed_list,max_speed)
        PICN_speed_list = []        
        
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        diag_Hit = ax.plot(Hit_speed,Hit_cdf,color='r',marker='x',linestyle='-',linewidth = 3,label='Proxy servers')
        diag_PICN = ax.plot(PICN_speed,PICN_cdf,color='g',linestyle='--',linewidth = 3,label='PICN caches')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_Hit[0],diag_PICN[0]),('Proxy servers','PICN caches'),loc=0,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'CDNHit_PICNPeers_CDF.pdf',format='PDF',dpi=5)
        #plt.show(fig,block=False)
        #plt.close(fig)
        
    def plot_CDN_PICN(self):
        
        
        print ('plot CDN_PICN...')
        listout = self.loadlist(self.out_path+'CDN_Hit')
        CDN_Hit_speed_list = [r['speed'] for r in listout]
        listout = []
        
        listout = self.loadlist(self.out_path+'CDN_Miss')
        CDN_Miss_speed_list = [r['speed'] for r in listout]
        listout = []
           
        CDN = CDN_Hit_speed_list + CDN_Miss_speed_list
        CDN_Hit_speed_list = []
        CDN_Miss_speed_list = []
        
        listout = self.loadlist(self.out_path+'p2p_local_list')
        PICN = [r['speed'] for r in listout]
        listout = []        
        listout = self.loadlist(self.out_path+'p2p_remote_list')
        for r in listout:
            PICN.append(r['speed'])
        listout = []
        listout = self.loadlist(self.out_path+'web_list')
        for r in listout:
            PICN.append(r['speed'])
        listout = []
                
                
        #print 'making ready for plotting cdf...'
        #print 'max(HIT_CDN)='+str(max(CDN))
        #print 'max(PICN)='+str(max(PICN))
        max_speed = max([max(CDN),max(PICN)])
        CDN_cdf,CDN_speed = self.cdf(CDN,max_speed)
        PICN_cdf,PICN_speed = self.cdf(PICN,max_speed)
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        diag_Hit = ax.plot(CDN_speed,CDN_cdf,color='r',marker='x',linewidth = 3,label='Proxy servers (Hit and Miss)')
        diag_PICN = ax.plot(PICN_speed,PICN_cdf,color='g',linestyle='--',linewidth = 3,label='PICN (Hit and Miss)')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_Hit[0],diag_PICN[0]),('proxy servers','PICN'),loc=0,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'CDN_PICN_CDF.pdf',format='PDF',dpi=5)
        
    def plot_PICN_overhead(self):
        print ('plot PICN overhead...')
        listout = self.loadlist(self.out_path+'web_list')
        PICN_Web_speed_list = [r['len']/float(r['latency']-r['overhead']) for r in listout]
        listout = []        
        
        listout = self.loadlist(self.out_path+'web_list')
        PICN_Miss_speed_list = [r['speed'] for r in listout]
        listout = []
        
               
        #print 'making ready for plotting cdf...'
        #print 'max(HIT_CDN)='+str(max(CDN))
        #print 'max(PICN)='+str(max(PICN))
        max_speed = max([max(PICN_Web_speed_list),max(PICN_Miss_speed_list)])
        PICN_Miss_cdf,PICN_Miss_speed = self.cdf(PICN_Miss_speed_list,max_speed)
        PICN_Web_cdf,PICN_Web_speed = self.cdf(PICN_Web_speed_list,max_speed)
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        diag_web = ax.plot(PICN_Web_speed,PICN_Web_cdf,color='r',marker='x',linewidth = 3,label='without PICN overhead')
        diag_miss = ax.plot(PICN_Miss_speed,PICN_Miss_cdf,color='g',linestyle='--',linewidth = 3,label='with PICN overhead')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_web[0],diag_miss[0]),('without PICN overhead','with PICN overhead'),loc=1,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'PICN_overhead.pdf',format='PDF',dpi=5)
        
    def plot_CDN_overhead(self):
        print ('plot CDN overhead...')
        listout = self.loadlist(self.out_path+'web_list')
        CDN_Web_speed_list = [r['len']/float(r['latency']-r['overhead']) for r in listout]
        listout = []        
        
        listout = self.loadlist(self.out_path+'CDN_Miss')
        CDN_Miss_speed_list = [r['speed'] for r in listout]
        listout = []
        
               
        #print 'making ready for plotting cdf...'
        #print 'max(HIT_CDN)='+str(max(CDN))
        #print 'max(PICN)='+str(max(PICN))
        max_speed = max([max(CDN_Web_speed_list),max(CDN_Miss_speed_list)])
        CDN_Miss_cdf,CDN_Miss_speed = self.cdf(CDN_Miss_speed_list,max_speed)
        CDN_Web_cdf,CDN_Web_speed = self.cdf(CDN_Web_speed_list,max_speed)
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='Helvetica', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        diag_web = ax.plot(CDN_Web_speed,CDN_Web_cdf,color='r',marker='x',linewidth = 3,label='without proxy servers overhead')
        diag_miss = ax.plot(CDN_Miss_speed,CDN_Miss_cdf,color='g',linestyle='--',linewidth = 3,label='with proxy servers overhead')
        ax.set_xlabel('Download speed (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_web[0],diag_miss[0]),('without proxy servers overhead','with proxy servers overhead'),loc=1,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'CDN_overhead.pdf',format='PDF',dpi=5)
        
    def plot_url_speed(self,folder_path, logNum, p2p_url_speed,p2p_url_remote_speed,web_url_speed):
        #print 'start making ready for ploting url_speed...'
        url_avgSpeed_localpeer = self.calculate_url_speed(self.url_set,p2p_url_speed)
        url_avgSpeed_remotepeer = self.calculate_url_speed(self.url_set,p2p_url_remote_speed)
        url_avgSpeed_web = self.calculate_url_speed(self.url_set,web_url_speed)
        self.dumpdict(folder_path+'p2p_local_url_speed_'+logNum ,url_avgSpeed_localpeer.keys(),url_avgSpeed_localpeer.values())
        self.dumpdict(folder_path+'p2p_remote_url_speed_'+logNum ,url_avgSpeed_remotepeer.keys(),url_avgSpeed_remotepeer.values())
        self.dumpdict(folder_path+'web_url_speed_'+logNum, url_avgSpeed_web.keys(),url_avgSpeed_web.values())
        #print 'making masks for plot url_speed'
        x = np.arange(len(url_avgSpeed_web.keys()))        
        y_web = np.array(url_avgSpeed_web.values()).astype(np.float)
        y_web_mask = np.isfinite(y_web)
        
        y_localp2p = np.array(url_avgSpeed_localpeer.values()).astype(np.float)
        y_localp2p_mask = np.isfinite(y_localp2p)
        
        y_remotep2p = np.array(url_avgSpeed_remotepeer.values()).astype(np.float)
        y_remotep2p_mask = np.isfinite(y_remotep2p)
        
        #print 'plotting url_speed...'
        fig, ax = plt.subplots()
        diag_p2p = ax.plot(x[y_localp2p_mask],y_localp2p[y_localp2p_mask],color='g',linestyle='--',linewidth = 3,label='local_p2p')
        diag_p2p_remote = ax.plot(x[y_remotep2p_mask],y_remotep2p[y_remotep2p_mask],color='b',linestyle='-.',linewidth = 3,label='remote_p2p')
        diag_web = ax.plot(x[y_web_mask],y_web[y_web_mask],color='k',marker='x',linewidth = 3,label='original web server')
        ax.set_ylabel('average download speed (Mb/s)')
        ax.set_xlabel('contents (URLs)')
        ax.set_title('Average download speed for different requested contents')
        ax.legend((diag_p2p[0],diag_p2p_remote[0],diag_web[0]),('local peer','remote peer','web server'),loc=0,fontsize=18) 
        fig.savefig(folder_path + logNum + '_url_avgspeed.pdf',format='PDF',dpi=5)
        plt.show(block=False)
        
    def redundancy(self,in_list):    
        max_list = max(in_list)
        interval_num = 100
        x = np.arange(0,max_list,max_list/interval_num)
        y = []
        y.append(0)
        for i in range(len(x)-1):
            y.append(len([a for a in in_list if a>x[i] and a<=x[i+1]]))        
        return x,y
        
    def plot_size(self):
        print ('plot size diagram...')  
        
        listout = self.loadlist(self.out_path+'p2p_local_list')
        print('list is loaded from the file')
        p2p_size_list = [r['len'] for r in listout]
        p2p_size_redundancy_x, p2p_size_redundancy_y= self.redundancy(p2p_size_list)
        listout = []
        p2p_size_list = []
        
        listout = self.loadlist(self.out_path+'web_list')
        web_size_list = [r['len'] for r in listout]
        web_size_redundancy_x, web_size_redundancy_y= self.redundancy(web_size_list)
        listout = []
        web_size_list = []

        plt.ion()       
#        x = np.arange(len(p2p_size_list))        
#        y_p2p = np.array(p2p_size_list.astype(np.int64))
#        y_p2p_mask = np.isfinite(y_p2p)
#        
#        y_web = np.array(web_size_list.astype(np.int64))
#        y_web_mask = np.isfinite(y_web)
        
        fig, ax = plt.subplots()
        diag_p2p = ax.plot(p2p_size_redundancy_x,p2p_size_redundancy_y,color='g',linestyle=':',label='p2p')
        diag_web = ax.plot(web_size_redundancy_x,web_size_redundancy_y,color='k',marker='.',label='web')
        ax.set_xlabel('requests')
        ax.set_ylabel('size')
        ax.legend((diag_p2p[0],diag_web[0]),('p2p','web'),loc=0,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'p2p_web_size.pdf',format='PDF',dpi=5)
        
        
    def plot_size_time(self, out_path, p2p_size_time, p2p_remote_size_time, web_size_time,pureweb_size_time,cdn_hit_size_time,cdn_miss_size_time):
        #print 'sortDict2List(p2p)'
        avg_size_p2p,maxsize_p2p,in_list_p2p = self.sortDict_2list(p2p_size_time)
        for l in in_list_p2p:
            print (str(l[0][0])+':')
            for speed in l[1:]:
                print (str(l[1][0])+', ')
            print ('\n')
        #print 'sortDict2List(p2pr)'
        avg_size_p2p_remote,maxsize_p2p_remote,in_list_p2p_remote = self.sortDict_2list(p2p_remote_size_time)
        #print 'sortDict2List(web)'
        avg_size_web,maxsize_web,in_list_web = self.sortDict_2list(web_size_time)
        avg_size_web,maxsize_web,in_list_web = self.sortDict_2list(web_size_time)
        _,_,in_list_pureweb = self.sortDict_2list(pureweb_size_time)        
        _,_,in_list_cdn_hit = self.sortDict_2list(cdn_hit_size_time)
        _,_,in_list_cdn_miss = self.sortDict_2list(cdn_miss_size_time)
        avg_size = min([avg_size_p2p,avg_size_p2p_remote,avg_size_web])
        maxsize = max([maxsize_p2p,maxsize_p2p_remote,maxsize_web])
        
        size_list, size_avgTime_localpeer = self.calculate_size_time(in_list_p2p, avg_size, maxsize)
        _,size_avgTime_remotepeer = self.calculate_size_time(in_list_p2p_remote, avg_size, maxsize)
        _,size_avgTime_web = self.calculate_size_time(in_list_web,avg_size, maxsize)
        _,size_avgTime_pureweb = self.calculate_size_time(in_list_pureweb,avg_size, maxsize)
        _,size_avgTime_cdn_hit = self.calculate_size_time(in_list_cdn_hit,avg_size, maxsize)
        _,size_avgTime_cdn_miss = self.calculate_size_time(in_list_cdn_miss,avg_size, maxsize)
        #print size_avgSpeed_localpeer
        
        fname = self.out_path + 'size_time.txt'
        with open(fname, 'w') as fout:
            for size in size_list:
                slen = str(size)
                fout.write ('size: '+slen + '\n')
                fout.write ( 'lpeer: ('+ str(size_avgTime_localpeer[slen][0])+\
                        ', '+ str(size_avgTime_localpeer[slen][1]) +')\n')
                fout.write ( 'rpeer: ('+ str(size_avgTime_remotepeer[slen][0])+\
                        ', '+ str(size_avgTime_remotepeer[slen][1]) +')\n')
                fout.write ( 'websr: ('+ str(size_avgTime_web[slen][0])+\
                        ', '+ str(size_avgTime_web[slen][1]) +')\n')
                fout.write ( 'p_hit: ('+ str(size_avgTime_cdn_hit[slen][0])+\
                        ', '+ str(size_avgTime_cdn_hit[slen][1]) +')\n')
                fout.write ( 'p_mis: ('+ str(size_avgTime_cdn_miss[slen][0])+\
                        ', '+ str(size_avgTime_cdn_miss[slen][1]) +')\n')
                fout.write ( 'pwebs: ('+ str(size_avgTime_pureweb[slen][0])+\
                        ', '+ str(size_avgTime_pureweb[slen][1]) +')\n\n')
        fout.close()
            
        #self.dumpdict(folder_path+'p2p_local_size_time_'+logNum ,size_list, size_avgSpeed_localpeer)
        #self.dumpdict(folder_path+'p2p_remote_size_time_'+logNum ,size_list, size_avgSpeed_remotepeer)
        #self.dumpdict(folder_path+'web_size_time_'+logNum, size_list, size_avgSpeed_web)
        
        
#        print 'making masks for plot 2'
#        x = np.arange(25)     
#        width = 0.1
#        fig , ax = plt.subplots()
#        diag_p2p = ax.bar(x,size_avgSpeed_localpeer, width, color= 'green')
#        diag_p2p_remote = ax.bar(x+width,size_avgSpeed_remotepeer, width, color= 'blue')
#        diag_web = ax.bar(x+width+width,size_avgSpeed_web, width, color= 'red')
#        ax.set_ylabel('download speed (Mb/s)')
#        ax.set_xlabel('content size class')
#        ax.set_title('Average download speed for different range of content size')
#        #ax.set_xticks(x+width/3)
#        #ax.set_xticklabels(str(size_list).strip('[]').split(','))
#        ax.legend((diag_p2p[0],diag_p2p_remote[0],diag_web[0]),('local peer','remote peer','web server')) 
#        fig.savefig(folder_path + logNum + '_size_avgspeed.pdf',format='PDF')
#        plt.show(block=False)
              
    def initializeFiles(self):
        open(self.out_path+'CDN_Hit', 'w').close()
        open(self.out_path+'CDN_Miss', 'w').close()
        open(self.out_path+'local_PICN', 'w').close()
        open(self.out_path+'local_CDN', 'w').close()
        open(self.out_path+'p2p_local_list', 'w').close()
        open(self.out_path+'p2p_remote_list', 'w').close()
        open(self.out_path+'web_list', 'w').close()
 
    def dumpAllFiles(self):
        CDN_hit_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==True] 
        self.dumplist(self.out_path+'CDN_Hit',CDN_hit_list)
        
        CDN_miss_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==False] 
        self.dumplist(self.out_path+'CDN_Miss',CDN_miss_list)
        self.reqList_CDN = []
        
        p2p_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==0] 
        self.dumplist(self.out_path+'p2p_local_list',p2p_list)
        #
        p2p_remote_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==1] 
        self.dumplist(self.out_path+'p2p_remote_list',p2p_remote_list)
      
        web_list = [{'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==2] 
        self.dumplist(self.out_path+'web_list',web_list)
        self.reqList = []
        
        self.dumplist(self.out_path+'local_PICN',self.local_list)
        self.dumplist(self.out_path+'local_CDN',self.local_CDN_list)
        
    def draw(self):
        self.plot_cdf_speed_PICN()
        self.plot_cdf_speed_CDN()
        self.plot_cdf_PICNPeers_CDNHit()
        #res.plot_size_time()
        self.plot_CDN_PICN()
        self.plot_PICN_overhead()
        self.plot_CDN_overhead()
        
        
    
    
if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("-o", "--out_path", dest="out_path",
                      help="output path for diagrams")
    (options, args) = parser.parse_args()
    res = Results(options.out_path)
   
    #res.plot_size()   
    res.plot_cdf_speed_PICN()
    res.plot_cdf_speed_CDN()
    res.plot_cdf_PICNPeers_CDNHit()
    #res.plot_size_time()
    res.plot_CDN_PICN()
    res.plot_PICN_overhead()
    res.plot_CDN_overhead()
    
    #plt.plot(res.p2p_size_time.keys())
    #plt.plot(Hit_size_time.keys())
    

