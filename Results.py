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
import math


class Results(object):
    def __init__(self, out_path):
        self.memBuffSize = 10000
        self.clients_upload = dict()
        self.reqList = [] #[URL,responseLen,responseTime,DL_speed,[localPeer=0,remorePeer=1,mainwebserver=2]]
        self.reqList_CDN = [] #[URL,responseLen,responseTime,DL_speed,Hit]
        self.pureWeb = []        
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
        
                    
        
        
    def add_Hit(self,timestamp, reqID,URL,responseLen,responseTime,webserverTime):
        
        speed = responseLen/float(responseTime)
        
        self.reqList_CDN.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'hit':True,'overhead':0})    
        if (len(self.reqList_CDN)>self.memBuffSize):
            CDN_hit_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==True] 
            self.dumplist(self.out_path+'CDN_Hit',CDN_hit_list)
            
            CDN_miss_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==False] 
            self.dumplist(self.out_path+'CDN_Miss',CDN_miss_list)
            self.reqList_CDN = []
        
            
                            
    #if provider=0 it is downloaded to pserver else if = 1 it is downloaded to client
    #if provider is 2 provider is original server
    def add_miss(self,timestamp,reqID,URL,responseLen,responseTime,webserverTime,provider):    
        #print("add miss",file=sys.stdout)  
        #print ('miss in CDN')
        if provider==2:
            self.reqList_CDN.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                    'speed':responseLen/float(responseTime),'hit':False,'overhead':responseTime-webserverTime})
            return
        speed = 0
        if self.CDN_reqID_times.has_key(reqID) :
            t = self.CDN_reqID_times.get(reqID)
            if t < responseTime:
                speed = responseLen/float(responseTime)
                self.CDN_reqID_times.update({reqID:responseTime})
                self.reqList_CDN.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                        'speed':speed,'hit':False,'overhead':responseTime-webserverTime})  
                self.CDN_miss = self.CDN_miss + 1
               #self.CDN_miss_size_time[str(responseLen)].append([responseTime,0])
            else:
                speed = responseLen/float(t)
                self.reqList_CDN.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':t,\
                        'speed':speed,'hit':False,'overhead':t-webserverTime})  
           
            return True
        else:
            self.CDN_reqID_times.update({reqID:responseTime})
            return False
        
    
    def add_localDL(self,timestamp, reqID,URL,responseLen):
        self.url_set.add(URL)
        self.local_list.append({'time':timestamp, 'URL':URL,'len':responseLen,'latency':0,\
                            'speed':0,'overhead':0})
        if(len(self.local_list)>self.memBuffSize):
            self.dumplist(self.out_path+'local_PICN',self.local_list)
            self.local_list = []
              
           
    def add_localDL_CDN(self,timestamp, reqID,URL,responseLen):
        self.local_CDN_list.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':0,\
                            'speed':0,'overhead':0})
  
        if(len(self.local_CDN_list)>self.memBuffSize):
            self.dumplist(self.out_path+'local_CDN',self.local_CDN_list)  
            self.local_CDN_list = []
                  
       
    def add_peerDL(self,timestamp, reqID,URL,responseLen,responseTime,overhead,isLocalpeer):
       
        self.url_set.add(URL)
        speed = responseLen/float(responseTime)
        if isLocalpeer:
            provider = 0
#            
        else:
            provider = 1
#            
        self.reqList.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'provider':provider,'overhead':overhead})
      
        if (len(self.reqList)>self.memBuffSize):
            p2p_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==0] 
            self.dumplist(self.out_path+'p2p_local_list',p2p_list)
            #
            p2p_remote_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==1] 
            self.dumplist(self.out_path+'p2p_remote_list',p2p_remote_list)
          
            web_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==2] 
            self.dumplist(self.out_path+'web_list',web_list)
            self.reqList = []
            
    def add_pureweb(self,timestamp, reqID, URL, responseLen, responseTime):
        self.pureWeb.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':responseLen/float(responseTime),'overhead':0})
        
        if (len(self.pureWeb)>self.memBuffSize):
            self.dumplist(self.out_path+'pure_web',self.pureWeb)
            self.pureWeb = []
            
    def add_webDL(self,timestamp, reqID, URL,responseLen,responseTime, overhead):
        
        self.url_set.add(URL)
        speed = responseLen/float(responseTime)        
        self.reqList.append({'time':timestamp,'URL':URL,'len':responseLen,'latency':responseTime,\
                            'speed':speed,'provider':2,'overhead':overhead})
       
    
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
        
    #sort the dictionary in form {size,[[latency,overhead],..]} based on size 
    #and return it in a new list in form [[[size,size][latency,overhead],...[latency,overhead]],...,[[size,size][latency,overhead],...[latency,overhead]]]
    #avg_size
    def sortDict_2list(self,in_dict,fname):
        #print 'call sortDict_2list'
        in_list = []
        avg_size = 0
        max_size = 0
        for a in in_dict.keys():
            #print a
            size = a
            avg_size = avg_size + size
            newlist = []
            for k in in_dict[a]:
                newlist.append(k)
            newlist.sort(key=lambda l: l[0])
            newlist.insert(0,[size,size])
            in_list.append(newlist)  
        #print (in_list[0])            
        size = in_list[0][0][0]
        in_list.sort(key=self.getKey)
        
        #print (in_list[len(in_list)-1])
        if len(in_list)>0:
            max_size = in_list[len(in_list)-1][0][0]
            avg_size = avg_size / float(len(in_list))
        #print 'max_size:' + str(max_size)
        else:
            max_size = 0
            avg_size = 0
        f=open('size_latency_'+fname+'.txt','w')
        for size in in_list:
            print(str(size[0][0]),file=f)
            for item in size[1:]:
                print(str(item[0])+', '+str(item[1])+': '+str(item[2]),file=f)
            print('\n',file=f)
        #print (in_list[len(in_list)-1])
        return avg_size,max_size,in_list
        
    def sortDict(self,in_dict):
        sorted_dict = {}
        for key in sorted(in_dict.iterkeys()):
            sorted_dict.update({key:in_dict[key]})
        return sorted_dict
        
    def calculate_size_time(self,in_list,max_size):
        #print 'call calculate_size_time'
        size_time = defaultdict()
        size_overhead = defaultdict()
        size_speed = defaultdict()
        size_list = []
        for i in range(0,int(math.log(max_size,2))+1):  #size in KB
            size_list.append(math.pow(2,i))

        i = 0
        sum_time = 0
        sum_overhead = 0
        sum_speed = 0
        n = 0
        #print size_list
        for length in size_list:
            while i<len(in_list) and in_list[i][0][0]<=length:
                #print l[0:]
                for time_overhead in in_list[i][1:]:
                    if time_overhead[0]>0:
                        sum_time = sum_time + time_overhead[0]
                        sum_overhead = sum_overhead + time_overhead[1]
                        sum_speed = sum_speed + time_overhead[2]
                        n = n + 1
                i = i + 1
            #print length,': ', n                
            if n > 0:
                size_time.setdefault(str(length),sum_time/float(n))
                size_overhead.setdefault(str(length), sum_overhead/float(n))
                size_speed.setdefault(str(length), sum_speed/float(n))
            else:
                size_time.setdefault(str(length),0)
                size_overhead.setdefault(str(length), 0)
                size_speed.setdefault(str(length), 0)
            n = 0
            sum_time = 0
            sum_overhead = 0
            sum_speed = 0
                        
        return size_list, size_time, size_overhead,size_speed
        
  
    def dumpdict(self,fname,dictkeys,dictvalues):
        with open(fname, 'w') as fout:
            for i in range(len(dictkeys)):
                fout.write( str(dictkeys[i])+ " : " + str(dictvalues[i]) +'\n')     
        fout.close() 
        
    def dumplist(self,fname,listname):
        with open(fname, 'a') as fout:
            while len(listname)>0:            
                r = listname.pop(0)
                print( str(r['time'])+ ' ' + str(r['URL']) + ' ' + str(r['speed']) + ' '+ str(r['len'])\
                + ' '+ str(r['latency'])+ ' '+ str(r['overhead']),file=fout)     
        fout.close() 
        
    def loadlist(self,fname):
        #print 'loading list '+fname
        fout = open(fname,'r')
        if fout==None:
            return None
        line = fout.readline()
        outList = []
        while (line):
            fields = line.split(' ')
            if len(fields)>=6:
                try:
                    speed = float(fields[2])
                except Exception as e:
                    print(e.message)
                else:
                    outList.append({'time':fields[0], 'URL':fields[1],'speed':speed,'len':int(fields[3]),\
                                    'latency':float(fields[4]),'overhead':float(fields[5])})
            line = fout.readline()
        fout.close() 
        return outList
        
    def cdf(self,vector,min_speed, max_speed):
        #max_size = min_speed#Kb/s
        interval_num = float(50)
        a=[]
        i = 1
        while(i<max_speed):
            i = i * 10
            if i<min_speed:
                continue
            a.append(i)
            
        end = 0
        x = np.array([])
        for r in a:
            max_size = r#KB/s
            step = (max_size-end)/interval_num
            xx = np.arange(end+step,max_size,step)
            x = np.append(x,xx)
            end = x[len(x)-1]
#       
#        interval_num = 300
#        x = np.arange(min_speed,max_speed,(max_speed-min_speed)/interval_num)
        y = []
        y.append(0)
        for i in range(len(x)-1):
            y.append(len([speed for speed in vector if speed>x[i] and speed<=x[i+1]]))
        
        cdf = np.cumsum(y)/float(np.sum(y))
        
        return cdf, x
    
    def plot_cdf_speed_PICN(self):
        print ('plot cdf_speed_PICN...')  
        
        print('calculating cdf of p2p')
        listout = self.loadlist(self.out_path+'p2p_local_list')
        print('list is loaded from the file')
        p2p_speed_list = [r['speed'] for r in listout]
        p2p_size = 0        
        for r in listout:
            p2p_size = p2p_size + r['len']
        listout = []
        p2pNum = len(p2p_speed_list)
                      
        print('calculating cdf of web')        
        listout = self.loadlist(self.out_path+'web_list')
        web_speed_list = [r['speed'] for r in listout]
        web_size = 0
        for r in listout:
            web_size = web_size + r['len']
        webNum = len (web_speed_list)
        listout = []
                
        print('calculating cdf of p2p_remote')
        listout = self.loadlist(self.out_path+'p2p_remote_list')
        p2p_remote_speed_list = [r['speed'] for r in listout]
        p2p_remote_size = 0
        for r in listout:
            p2p_remote_size = p2p_remote_size + r['len']
        listout = []
        p2p_remoteNum = len(p2p_remote_speed_list)
        
        print('calculating cdf of pure web')
        listout = self.loadlist(self.out_path+'pure_web')
      
#        pure_web_list = [r['speed'] for r in listout]
#        pure_web_size = 0
#        for r in listout:
#            pure_web_size = pure_web_size + r['len']
#        listout = []
        
        p2p_max = max(p2p_speed_list)
        p2p_remote_max = max(p2p_remote_speed_list)
        web_max = max(web_speed_list)
#        pure_web_max = max(pure_web_list)
        p2p_min = min(p2p_speed_list)
        p2p_remote_min = min(p2p_remote_speed_list)
        web_min = min(web_speed_list)
#        pure_web_min = min(pure_web_list)
        
        #max_speed = max([p2p_min,p2p_remote_max,web_max,pure_web_max])
        max_speed = max([p2p_max,p2p_remote_max,web_max])#,pure_web_max])
        
        print()
        print(p2p_max)
        print(p2p_remote_max)
        print(web_max)
#        print(pure_web_max)
        print()
        print(p2p_min)
        print(p2p_remote_min)
        print(web_min)
#        print(pure_web_min)
        
        p2p_cdf,p2p_speed = self.cdf(p2p_speed_list,max_speed,p2p_max)
        p2p_speed_list = []          
        web_cdf,web_speed = self.cdf(web_speed_list,max_speed,web_max)
        web_speed_list = []
        p2p_remote_cdf,p2p_remote_speed = self.cdf(p2p_remote_speed_list,max_speed,p2p_remote_max)
        p2p_remote_speed_list = []    
#        pure_web_cdf,pure_web_speed = self.cdf(pure_web_list,max_speed,pure_web_max)
#        pure_web_list = []  
        
        
        
        listout = self.loadlist(self.out_path+'local_PICN')
        localNum = len(listout)
        local_size = 0
        for r in listout:
            local_size = local_size + r['len']
        listout = []
        
        f = open(self.out_path + 'info.txt','a')
        tot_supported = p2pNum + p2p_remoteNum + webNum + localNum
        tot_size = p2p_remote_size + p2p_size + local_size + web_size#pure_web_size
        tot_hit_size = p2p_remote_size + p2p_size + local_size
        print ('\nTotal number of supported requests: ' + str(tot_supported),file=f)
        print ('Hit ratio in local cache in PICN: ' + str(round(localNum/float(tot_supported)*100,2)),file=f)
        print ('Hit ratio in local peer in PICN: ' + str(round(p2pNum/float(tot_supported)*100,2)),file=f)
        print ('Hit ratio in remote peer in PICN: ' + str(round(p2p_remoteNum/float(tot_supported)*100,2)),file=f)
        print ('Miss ratio in PICN: ' + str(round(webNum/float(tot_supported)*100,2)),file=f)
        print ('Total hit ratio in in PICN (except local): ' + str(round((p2p_remoteNum+p2pNum)/float(tot_supported)*100,2)),file=f)
        print ('Total hit ratio in in PICN : ' + str(round((p2p_remoteNum+p2pNum+localNum)/float(tot_supported)*100,2)),file=f)
        print ('\nTotal traffic: ' +  str(tot_size), file=f)
        print ('saved external traffic in local peers: ' +  str(round(p2p_size/float(tot_size)*100,2)), file=f)
        print ('saved external traffic in remote peers: ' +  str(round(p2p_remote_size/float(tot_size)*100,2)), file=f)
        print ('saved external traffic in local machines: ' +  str(round(local_size/float(tot_size)*100,2)), file=f)
        print ('total saved external traffic in PICN: (except local)' +  str(round((p2pNum+p2p_remoteNum)/float(tot_size)*100,2)), file=f)
        print ('total saved external traffic in PICN:'+str(round(tot_hit_size/float(tot_size)*100,2)),file=f)
        print ('missed traffic in PICN : ' + str(round(web_size/float(tot_size)*100,2)),file=f)
        
        f.close()
        #print 'plotting speed cdf...'
        plt.ion()
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)   
        n = len(p2p_speed)
        diag_p2p = ax.plot(p2p_speed[0:n],p2p_cdf[0:n],color='g',linestyle='--',marker='',linewidth = 3,label='Local peers (via PICN)')
        diag_p2p_remote = ax.plot(p2p_remote_speed[0:n],p2p_remote_cdf[0:n],color='b',linestyle='-.',marker='',linewidth = 3,label='Remote peers (via PICN)')
        diag_web = ax.plot(web_speed[0:n],web_cdf[0:n],color='r',marker='',linestyle=':',linewidth = 3,label='missed in picn')
#        diag_pureweb = ax.plot(pure_web_speed[0:n],pure_web_cdf[0:n],color='k',marker='',linestyle='-',linewidth = 3,label='with out picn')
        ax.set_xscale('log')
        ax.set_xlabel('Transfer rate (Mb/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
#        ax.legend((diag_p2p[0],diag_p2p_remote[0],diag_web[0],diag_pureweb[0]),('Hit in Local peers','Hit in remote peers','Miss in PICN','Without PICN'),loc=0,fontsize=18) 
        ax.legend((diag_p2p[0],diag_p2p_remote[0],diag_web[0]),('Hit in Local peers','Hit in remote peers','Miss in PICN'),loc=0,fontsize=18) 
        fig.savefig(self.out_path + 'PICN_CDF.pdf',format='PDF',dpi=5)
        
    def calculate_speed_cdf(self,proxy):
        print ('plot cdf_speed...')
        if proxy:
            listout = self.loadlist(self.out_path+'CDN_Hit')
            cdn_hit_num = len(listout)
            CDN_Hit_speed_list = [r['speed'] for r in listout]
            hit_size = 0
            for r in listout:
                hit_size = hit_size + r['len']
            listout = []
            
            listout = self.loadlist(self.out_path+'CDN_Miss')
            cdn_miss_num = len (listout)
            CDN_Miss_speed_list = [r['speed'] for r in listout]
            miss_size = 0
            for r in listout:
                miss_size = miss_size + r['len']
            listout = []
            
            listout = self.loadlist(self.out_path+'local_CDN')
            if listout!=None:
                cdn_local_num = len (listout)
                cdn_local_size = 0
                for r in listout:
                    cdn_local_size = cdn_local_size + r['len']
            else:
                cdn_local_num = 0
                cdn_local_size = 0
            listout = []
            
            CDN_Miss_max = max(CDN_Miss_speed_list)
            CDN_Hit_max = max(CDN_Hit_speed_list)
            CDN_Miss_min = min(CDN_Miss_speed_list)
            CDN_Hit_min = min(CDN_Hit_speed_list)
            
        
        print('calculating cdf of p2p')
        listout = self.loadlist(self.out_path+'p2p_local_list')
        print('list is loaded from the file')
        p2p_speed_list = [r['speed'] for r in listout]
        p2p_size = 0        
        for r in listout:
            p2p_size = p2p_size + r['len']
        listout = []
        p2pNum = len(p2p_speed_list)
                      
        print('calculating cdf of web')        
        listout = self.loadlist(self.out_path+'web_list')
        web_speed_list = [r['speed'] for r in listout]
        web_size = 0
        for r in listout:
            web_size = web_size + r['len']
        webNum = len (web_speed_list)
        listout = []
                
        print('calculating cdf of p2p_remote')
        listout = self.loadlist(self.out_path+'p2p_remote_list')
        p2p_remote_speed_list = [r['speed'] for r in listout]
        p2p_remote_size = 0
        for r in listout:
            p2p_remote_size = p2p_remote_size + r['len']
        listout = []
        p2p_remoteNum = len(p2p_remote_speed_list)
        
        listout = self.loadlist(self.out_path+'local_PICN')
        local_list = [r['speed'] for r in listout]
        local_size = 0
        for r in listout:
            local_size += r['len']
        listout = []
        local_Num = len(local_list)
        
        print('calculating cdf of pure web')        
        listout = self.loadlist(self.out_path+'pure_web')
        pweb_speed_list = [r['speed'] for r in listout]
        pweb_size = 0
        for r in listout:
            pweb_size = pweb_size + r['len']
        pwebNum = len (pweb_speed_list)
        listout = []
        p2p_max = max(p2p_speed_list)
        p2p_remote_max = max(p2p_remote_speed_list)
        pweb_max = max(pweb_speed_list)
#        picn_miss_max = max(web_speed_list)
#        p2p_min = min(p2p_speed_list)
#        p2p_remote_min = min(p2p_remote_speed_list)
#        picn_miss_min = min(web_speed_list)
#        pweb_min = min(pweb_speed_list)
        print('p2p max speed: ', p2p_max)
        print('rp2p max speed',p2p_remote_max)
        print('pureweb max speed',pweb_max)

     
#        if proxy:
#            max_speed = max([CDN_Miss_max,CDN_Hit_max,p2p_max,p2p_remote_max,picn_miss_max])
#            min_speed = min([CDN_Miss_min,CDN_Hit_min,p2p_min,p2p_remote_min,picn_miss_min])
#            Hit_cdf,Hit_speed = self.cdf(CDN_Hit_speed_list,CDN_Hit_min,CDN_Hit_max)
#            CDN_Hit_speed_list = []
#            Miss_cdf,Miss_speed = self.cdf(CDN_Miss_speed_list,CDN_Miss_min,CDN_Miss_max)
#            CDN_Miss_speed_list = [] 
#        else:
#            max_speed = max([p2p_max,p2p_remote_max,picn_miss_max,pweb_max])
#            min_speed = min([p2p_min,p2p_remote_min,picn_miss_min,pweb_min])
#        p2p_cdf,p2p_speed = self.cdf(p2p_speed_list,p2p_min,p2p_max)
#        p2p_speed_list = []          
#        web_cdf,web_speed = self.cdf(web_speed_list,picn_miss_min,picn_miss_max)
#        web_speed_list = []
#        p2p_remote_cdf,p2p_remote_speed = self.cdf(p2p_remote_speed_list,p2p_remote_min,p2p_remote_max)
#        p2p_remote_speed_list = [] 
#        pweb_cdf,pweb_speed = self.cdf(pweb_speed_list,pweb_min,pweb_max)
#        pweb_speed_list = [] 
#              
        f = open(self.out_path + 'info.txt','a')
        tot_supported = p2pNum + p2p_remoteNum + webNum + local_Num 
        tot_size = p2p_remote_size + p2p_size + web_size + local_size#pure_web_size
        print ('\nTotal number of requests: ' + str(pwebNum),file=f)
        print ('\nTotal number of supported requests: ' + str(tot_supported),file=f)
        print ('Total traffic : ' +  str(tot_size), file=f)
        if proxy:        
            tot_hit_size = hit_size + cdn_local_size
            print ('\nHit ratio in proxy servers: ' + str(round(cdn_hit_num/float(tot_supported)*100,2)),file=f)
            if cdn_local_num>0:
                print ('Hit ratio in local machines connected to proxy servers: ' + str(round(cdn_local_num/float(tot_supported)*100,2)),file=f)
            print ('Total hit ratio in proxy servers(+local machines): ' + str(round((cdn_hit_num+cdn_local_num)/float(tot_supported)*100,2)),file=f)
            print ('Miss ratio in proxy servers: ' + str(round(cdn_miss_num/float(tot_supported)*100,2)),file=f)
            print ('External traffic saved in proxy servers(+local machines): ' + str(round(tot_hit_size/float(tot_size)*100,2)),file=f)
            print ('External traffic saved in proxy servers: ' + str(round(hit_size/float(tot_size)*100,2)),file=f)
            print ('External traffic saved in local machines in proxy servers: ' + str(round(cdn_local_size/float(tot_size)*100,2)),file=f)
            print ('Miss traffic in proxy servers: ' + str(round(miss_size/float(tot_size)*100,2)),file=f)
        tot_hit_size = p2p_remote_size + p2p_size + local_size
        print ('\nHit ratio in local machine in PICN: ' + str(round(local_Num/float(tot_supported)*100,3)),file=f)
        print ('Hit ratio in local peer in PICN: ' + str(round(p2pNum/float(tot_supported)*100,3)),file=f)
        print ('Hit ratio in remote peer in PICN: ' + str(round(p2p_remoteNum/float(tot_supported)*100,3)),file=f)
        print ('Miss ratio in PICN: ' + str(round(webNum/float(tot_supported)*100,3)),file=f)
        print ('Total hit ratio in PICN (except local): ' + str(round((p2p_remoteNum+p2pNum)/float(tot_supported)*100,3)),file=f)
        print ('Total hit ratio in PICN : ' + str(round((p2p_remoteNum+p2pNum+local_Num)/float(tot_supported)*100,3)),file=f)
        print ('saved external traffic in local peers: ' +  str(round(p2p_size/float(tot_size)*100,3)), file=f)
        print ('saved external traffic in local machines: ' +  str(round(local_size/float(tot_size)*100,3)), file=f)
        print ('saved external traffic in remote peers: ' +  str(round(p2p_remote_size/float(tot_size)*100,3)), file=f)
        print ('total saved external traffic in PICN:'+str(round(tot_hit_size/float(tot_size)*100,3)),file=f)
        print ('missed traffic in PICN : ' + str(round(web_size/float(tot_size)*100,3)),file=f)
        f.close()
#        if proxy is not True:
#            Hit_speed= Hit_cdf = Miss_speed = Miss_cdf = None
#        elif cdn_local_num==0:
#            Hit_speed= Hit_cdf = Miss_speed = Miss_cdf = None
        #return [Hit_speed,Hit_cdf],[Miss_speed,Miss_cdf],[p2p_speed,p2p_cdf],[p2p_remote_speed,p2p_remote_cdf],[web_speed,web_cdf],[pweb_speed,pweb_cdf]
        
        
    def plot_cdf_proxy_picn(self, proxy_hit, proxy_miss, picn_p2p, picn_rp2p, picn_miss,pure_web):
        #print 'plotting speed cdf...'
        plt.ion()
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font) 
        #n = len(proxy_hit[0])
        diag_hit_proxy = ax.plot(proxy_hit[0],proxy_hit[1],color='y',linestyle='--',marker='.',linewidth = 3)
        diag_miss_proxy = ax.plot(proxy_miss[0],proxy_miss[1],color='k',linestyle='-',linewidth = 3)
        diag_p2p = ax.plot(picn_p2p[0],picn_p2p[1],color='g',linestyle='--',linewidth = 3)
        diag_rp2p = ax.plot(picn_rp2p[0],picn_rp2p[1],color='b',linestyle='-.',linewidth = 3)
        diag_miss_picn = ax.plot(picn_miss[0],picn_miss[1],color='r',linestyle=':',linewidth = 3)
        diag_pure_web = ax.plot(pure_web[0],pure_web[1],color='k',linestyle='-.',linewidth = 3)
        
        ax.set_xscale('log')
        ax.set_xlabel('Transfer rate (KB/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_hit_proxy[0],diag_miss_proxy[0], diag_p2p[0],diag_rp2p[0],diag_miss_picn[0],diag_pure_web[0]),
                  ('Hit in proxy servers','Miss in proxy servers', 'Hit in local peers in PICN',
                  'Hit in remote peers in PICN','Miss in PICN','Without PICN or proxy'),loc=0,fontsize=18)
        fig.savefig(self.out_path + 'proxy_picn_CDF.pdf',format='PDF',dpi=5)
        
    def plot_cdf_picn(self, picn_p2p, picn_rp2p, picn_miss,pure_web):
        #print 'plotting speed cdf...'
        plt.ion()
        fig, ax = plt.subplots()
        plt.gcf().subplots_adjust(bottom=0.15)
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font) 
        #n = len(proxy_hit[0])
#        diag_p2p = ax.plot(picn_p2p[0],picn_p2p[1],color='g',linestyle='--',linewidth = 3)
#        diag_rp2p = ax.plot(picn_rp2p[0],picn_rp2p[1],color='b',linestyle='-.',linewidth = 3)
#        diag_miss_picn = ax.plot(picn_miss[0],picn_miss[1],color='r',linestyle=':',linewidth = 3)
#        diag_pweb = ax.plot(pure_web[0],pure_web[1],color='k',linestyle='-',linewidth = 3)
        
        diag_p2p = ax.plot(picn_p2p[0],picn_p2p[1],color='g',marker='o', linestyle='-',linewidth = 3)
        diag_rp2p = ax.plot(picn_rp2p[0],picn_rp2p[1],color='b',marker='^', linestyle='-',linewidth = 3)
        diag_miss_picn = ax.plot(picn_miss[0],picn_miss[1],color='r', linestyle='--',linewidth = 3)
        diag_pweb = ax.plot(pure_web[0],pure_web[1],color='k', linestyle='-',linewidth = 3)
        
        ax.set_xscale('log')
        ax.set_xlabel('Transfer rate (KB/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_p2p[0],diag_rp2p[0],diag_miss_picn[0],diag_pweb[0]),
                  ('Hit in local peers','Hit in remote peers','Miss in PICN','Without PICN' ),
                    loc=2,fontsize=18)
#        ax.legend((diag_p2p[0],diag_rp2p[0],diag_miss_picn[0]),
#                  ('Hit in local peers','Hit in remote peers','Miss in PICN'),
#                    loc=2,fontsize=18)
        fig.savefig(self.out_path + 'picn_CDF.pdf',format='PDF',dpi=5)
        
    
    def plot_PICN_overhead(self):
        print ('plot PICN overhead...')
        listout = self.loadlist(self.out_path+'web_list')
        PICN_Web_speed_list = [r['len']/float(r['latency']-r['overhead']) for r in listout]
        
        PICN_Miss_speed_list = [r['speed'] for r in listout]
        listout = []
        
               
        #print 'making ready for plotting cdf...'
        #print 'max(HIT_CDN)='+str(max(CDN))
        #print 'max(PICN)='+str(max(PICN))
        PICN_web_max = max(PICN_Web_speed_list)
        PICN_Miss_max = max(PICN_Miss_speed_list)
        max_speed = max([PICN_web_max, PICN_Miss_max])
        PICN_Miss_cdf,PICN_Miss_speed = self.cdf(PICN_Miss_speed_list,max_speed,PICN_Miss_max)
        PICN_Web_cdf,PICN_Web_speed = self.cdf(PICN_Web_speed_list,max_speed,PICN_web_max)
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        n = len(PICN_Web_speed)
        diag_web = ax.plot(PICN_Web_speed[0:n],PICN_Web_cdf[0:n],color='k',marker='',linestyle='-',linewidth = 3,label='without PICN overhead')
        diag_miss = ax.plot(PICN_Miss_speed[0:n],PICN_Miss_cdf[0:n],color='r',linestyle=':',linewidth = 3,label='with PICN overhead')
        ax.set_xscale('log')
        ax.set_xlabel('Transfer rate (KB/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_web[0],diag_miss[0]),('Without PICN overhead','With PICN overhead'),loc=1,fontsize=18)
        #ax.legend((diag_p2p[0],diag_p2p_remote[0]),('local peer','remote peer')) 
        fig.savefig(self.out_path + 'PICN_overhead.pdf',format='PDF',dpi=5)
        
    def plot_CDN_overhead(self):
        print ('plot CDN overhead...')
        
        listout = self.loadlist(self.out_path+'CDN_Miss')
        CDN_Miss_speed_list = [r['speed'] for r in listout]
        CDN_Web_speed_list = [r['len']/float(r['latency']-r['overhead']) for r in listout]
        listout = []
               
        #print 'making ready for plotting cdf...'
        #print 'max(HIT_CDN)='+str(max(CDN))
        #print 'max(PICN)='+str(max(PICN))
        CDN_web_max = max(CDN_Web_speed_list)
        CDN_Miss_max = max(CDN_Miss_speed_list)
        max_speed = max([CDN_web_max,CDN_Miss_max])
        CDN_Miss_cdf,CDN_Miss_speed = self.cdf(CDN_Miss_speed_list,max_speed,CDN_Miss_max)
        CDN_Web_cdf,CDN_Web_speed = self.cdf(CDN_Web_speed_list,max_speed,CDN_web_max)
        #print 'plotting speed cdf...'
        plt.ion()        
        fig, ax = plt.subplots()
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=20, weight='normal', stretch='normal')
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)  
        n = len(CDN_Web_cdf)
        diag_web = ax.plot(CDN_Web_speed[0:n],CDN_Web_cdf[0:n],color='k',marker='',linestyle='-',linewidth = 3,label='without proxy servers overhead')
        diag_miss = ax.plot(CDN_Miss_speed[0:n],CDN_Miss_cdf[0:n],color='r',linestyle=':',linewidth = 3,label='with proxy servers overhead')
        ax.set_xscale('log')
        ax.set_xlabel('Transfer rate (KB/s)',fontsize=20)
        ax.set_ylabel('CDF of transfer rate',fontsize=20)
        ax.legend((diag_web[0],diag_miss[0]),('Without proxy servers overhead','With proxy servers overhead'),loc=1,fontsize=18)
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
        ax.set_ylabel('average download speed (KB/s)')
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
        
     
    def plot_bar(self,x_labels,bars, y_label, names,color, hatch,fileName) :
        bars_val = []
        for i in range(len(bars)):       
            bars_val.append([])
        
        xtick=[]
        for key in x_labels:
            xtick.append(int(key))
            for i in range(len(bars_val)):
                bars_val[i].append(bars[i][str(key)])
            
     
        N = len(x_labels)
        ind = np.arange(N)  # the x locations for the links

        width = 4           # the width of the bars
        #k = len(bars)
        for i in range(N):
            ind[i] = i*(len(bars)+1)*width
        print(ind[0])
        print(ind[1])
        print(ind[2])
        fig, ax = plt.subplots()
        plt.gcf().subplots_adjust(bottom=0.2)
        ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=15, weight='normal', stretch='normal')
                    
        for label in ax.get_xticklabels():
            label.set_fontproperties(ticks_font)
        for label in ax.get_yticklabels():
            label.set_fontproperties(ticks_font)
    
        rects=[]
        for i in range(len(bars_val)):
            rects.append(ax.bar(ind +i*width, bars_val[i][0:N], width, color=color[i],hatch=hatch[i]))
            
                
        # add some text for labels, title and axes ticks
        ax.set_ylabel(y_label, fontsize=20)
        ax.set_xlabel('average size (KB)',fontsize=20)
        ax.set_yscale('log')
        ax.set_xticklabels(xtick[0:N], rotation=90)
        ax.set_xticks(ind + len(bars)*width/2)
        
        ax.legend(rects, names,loc=0)
        plt.savefig(self.out_path + fileName)
        plt.clf()    
        
    def calculate_improvement(self,picn, pure_web,function):
        summ = 0
        maxx = 0
        num = 0
        for key in picn.keys():
            if key> 2:  #to be sure of improvement
                improvement = abs(picn[key] - pure_web[key])/max(picn[key],pure_web[key])
                summ += improvement
                num += 1
                if improvement>maxx:
                    maxx = improvement
        max_improvement = round(maxx*100,2)
        avg_improvement = round(summ /float(num)*100,2)
        return max_improvement,avg_improvement
        
    def plot_size_time(self,proxy):
        listout = self.loadlist(self.out_path + 'p2p_local_list')
        p2p_size_time = defaultdict()
        for r in listout:                                               #s,ms,KB/s
            p2p_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
        picn_size_time = p2p_size_time     
        listout = []
        listout = self.loadlist(self.out_path + 'p2p_remote_list')
        p2p_remote_size_time = defaultdict()
        for r in listout:
            p2p_remote_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
            picn_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
            
        
        listout = []
        listout = self.loadlist(self.out_path + 'web_list')
        web_size_time = defaultdict()
        for r in listout:
            web_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
          
        
        listout = []
        listout = self.loadlist(self.out_path + 'pure_web')
        pure_web_size_time = defaultdict()
        for r in listout:
            pure_web_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
        
        if proxy:
            listout = []
            listout = self.loadlist(self.out_path + 'CDN_Hit')
            cdn_hit_size_time = defaultdict()
            for r in listout:
                cdn_hit_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
            
            listout = []
            listout = self.loadlist(self.out_path + 'CDN_Miss')
            cdn_miss_size_time = defaultdict()
            for r in listout:
                cdn_miss_size_time.setdefault(r['len']/float(1000), []).append([r['latency']/1000,r['overhead'],r['speed']])
            avg_size_cdn_hit,maxsize_cdn_hit,in_list_cdn_hit = self.sortDict_2list(cdn_hit_size_time,'cdn_hit')
            avg_size_cdn_miss,maxsize_cdn_miss,in_list_cdn_miss = self.sortDict_2list(cdn_miss_size_time,'cdn_miss')
                    
        avg_size_picn,maxsize_picn,in_list_picn = self.sortDict_2list(picn_size_time,'picn')
        avg_size_p2p,maxsize_p2p,in_list_p2p = self.sortDict_2list(p2p_size_time,'p2p')
        avg_size_p2p_remote, maxsize_p2p_remote,in_list_p2p_remote = self.sortDict_2list(p2p_remote_size_time,'rp2p')
        avg_size_web,maxsize_web,in_list_web = self.sortDict_2list(web_size_time,'miss_picn')
        avg_size_pure_web,maxsize_pure_web,in_list_pure_web = self.sortDict_2list(pure_web_size_time,'pureweb')
        maxsize = maxsize_picn #max([maxsize_p2p,maxsize_p2p_remote])
        if proxy:
            size_list_cdn,size_avgTime_cdn_hit,size_overhead_cdn_hit = self.calculate_size_time(in_list_cdn_hit,maxsize)
            _,size_avgTime_cdn_miss,size_overhead_cdn_miss = self.calculate_size_time(in_list_cdn_miss, maxsize)
        
        size_list_picn, size_avgTime_localpeer,size_overhead_localpeer,size_speed_localpeer = self.calculate_size_time(in_list_p2p, maxsize)
        _,size_avgTime_remotepeer,size_overhead_remotepeer,size_speed_remotepeer = self.calculate_size_time(in_list_p2p_remote, maxsize)
        _,size_avgTime_picn,size_overhead_picn,size_speed_picn = self.calculate_size_time(in_list_picn, maxsize)
        _,size_avgTime_web,size_overhead_web,size_speed_web = self.calculate_size_time(in_list_web, maxsize)
        _,size_avgTime_pure_web,size_overhead_pure_web,size_speed_pure_web = self.calculate_size_time(in_list_pure_web, maxsize)
        
        
        fname = self.out_path + 'size_time.txt'
        with open(fname, 'w') as fout:
            for size in size_list_picn:
                slen = str(size)
                fout.write ('size: '+slen + '\n')
                fout.write ( 'lpeer: ('+ str(size_avgTime_localpeer[slen])+\
                        ', '+ str(size_overhead_localpeer[slen]) +')\n')
                fout.write ( 'rpeer: ('+ str(size_avgTime_remotepeer[slen])+\
                        ', '+ str(size_overhead_remotepeer[slen]) +')\n')
                fout.write ( 'missed_picn: ('+ str(size_avgTime_web[slen])+\
                        ', '+ str(size_overhead_web[slen]) +')\n')
                fout.write ( 'pure_web: ('+ str(size_avgTime_pure_web[slen])+\
                        ', '+ str(size_overhead_pure_web[slen]) +')\n')
                if proxy:
                    fout.write ( 'hit_proxy: ('+ str(size_avgTime_cdn_hit[slen])+\
                        ', '+ str(size_overhead_cdn_hit[slen]) +')\n')
                    fout.write ( 'miss_proxy: ('+ str(size_avgTime_cdn_miss[slen])+\
                        ', '+ str(size_overhead_cdn_miss[slen]) +')\n')
           
        fout.close()
        max_latency_improvement,avg_latency_improvement = self.calculate_improvement(size_avgTime_picn, size_avgTime_pure_web,min)
        max_speed_improvement, avg_speed_improvement = self.calculate_improvement(size_speed_picn, size_speed_pure_web,max)
        self.plot_bar(size_list_picn,[size_avgTime_localpeer,size_avgTime_remotepeer,size_avgTime_web,size_avgTime_pure_web],'Latency (s)',
                      ['Hit in local peers','Hit in remote peers','Miss in PICN','Without PICN'],['g','b','r','0.75'],['---','...','xx','///'],'size_time_picn_detail.pdf') 
        self.plot_bar(size_list_picn,[size_avgTime_picn,size_avgTime_pure_web],'Latency (s)',
                      ['Hit in PICN cache storages','Without PICN'],['g','0.75'],['---','///'],'size_time_picn.pdf') 
        self.plot_bar(size_list_picn,[size_speed_localpeer,size_speed_remotepeer,size_speed_web,size_speed_pure_web],'speed (KB/s)',
                      ['Hit in local peers','Hit in remote peers','Miss in PICN','Without PICN'],['g','b','r','0.75'],['---','...','xx','///'],'size_speed_picn_detail.pdf') 
        
        if proxy:
            self.plot_bar(size_list_picn,[size_avgTime_cdn_hit,size_avgTime_localpeer],
                      ['Hit in proxy servers','Hit in local peers', 'Without PICN'],['y','g','0.75'],['.','-','//'],'size_time_cdn.pdf') 
        f = open(self.out_path + 'info.txt','a')
        print('Maximum Latency improvement: '+str( max_latency_improvement),file=f)
        print('Average Latency improvement: '+str( avg_latency_improvement),file=f)
        print('Maximum speed improvement: '+str( max_speed_improvement),file=f)
        print('Average speed improvement: '+str( avg_speed_improvement),file=f)
        
              
    def initializeFiles(self):
        open(self.out_path+'CDN_Hit', 'w').close()
        open(self.out_path+'CDN_Miss', 'w').close()
        open(self.out_path+'local_PICN', 'w').close()
        open(self.out_path+'local_CDN', 'w').close()
        open(self.out_path+'p2p_local_list', 'w').close()
        open(self.out_path+'p2p_remote_list', 'w').close()
        open(self.out_path+'web_list', 'w').close()
        open(self.out_path+'pure_web', 'w').close()
 
    def dumpAllFiles(self,proxy):
        if proxy:
            CDN_hit_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==True] 
            self.dumplist(self.out_path+'CDN_Hit',CDN_hit_list)
            
            CDN_miss_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
            'len':req['len'],'overhead':req['overhead']} for req in self.reqList_CDN if req['hit']==False] 
            self.dumplist(self.out_path+'CDN_Miss',CDN_miss_list)
            self.reqList_CDN = []
            self.dumplist(self.out_path+'local_CDN',self.local_CDN_list)
            
                   
        p2p_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==0] 
        self.dumplist(self.out_path+'p2p_local_list',p2p_list)
        #
        p2p_remote_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==1] 
        self.dumplist(self.out_path+'p2p_remote_list',p2p_remote_list)
      
        web_list = [{'time':req['time'],'URL':req['URL'],'speed':req['speed'],'latency':req['latency'],\
        'len':req['len'],'overhead':req['overhead']} for req in self.reqList if req['provider']==2] 
        self.dumplist(self.out_path+'web_list',web_list)
        self.reqList = []
  
        self.dumplist(self.out_path+'pure_web',self.pureWeb)
        self.dumplist(self.out_path+'local_PICN',self.local_list)
        
        
    def draw(self,proxy):
        self.calculate_speed_cdf(proxy)
        self.plot_size_time(proxy)
    
#        proxy_hit, proxy_miss, picn_p2p, picn_rp2p, picn_miss, pure_web = self.calculate_speed_cdf(proxy)
#        self.plot_cdf_picn(picn_p2p,picn_rp2p,picn_miss,pure_web)    
#        if proxy:
#            if proxy_hit[0]!=None:
#                self.plot_cdf_proxy_picn(proxy_hit, proxy_miss, picn_p2p, picn_rp2p, picn_miss)
         #res.plot_cdf_proxy(proxy_hit,proxy_miss)
            
        
    def plot_size_time_detail(self):
        listout = self.loadlist(self.out_path + 'p2p_local_list')
        p2p_size_time = defaultdict()
        for r in listout:
            p2p_size_time.setdefault(r['len'], [[r['latency'],r['overhead']]]).append([r['latency'],r['overhead']])
        
        listout = []
        listout = self.loadlist(self.out_path + 'pure_web')
        pure_web_size_time = defaultdict()
        for r in listout:
            pure_web_size_time.setdefault(r['len'], [[r['latency'],r['overhead']]]).append([r['latency'],r['overhead']])
        listout = []            
        
        avg_size_p2p,maxsize_p2p,in_list_p2p = self.sortDict_2list(p2p_size_time)
        avg_size_pure_web,maxsize_pure_web,in_list_pure_web = self.sortDict_2list(pure_web_size_time)
        f= open('p2p_size','w')
        for l in in_list_p2p:
            print (l,file=f)
            print ('\n\n',file=f)
        f.close()
        f= open('pureweb_size','w')
        for l in in_list_pure_web:
            print (l,file=f)
            print ('\n\n',file=f)
        f.close()
        p2p = []        
        pureweb = []   
        m = 0
        print (maxsize_p2p)
        print (maxsize_pure_web)
       
        for s in in_list_pure_web:
            if s[0][0]>maxsize_p2p:
                print('*')
                break
            #print (s[0][0])
            for t in s[1:]:
                pureweb.append(t[0])
            ss = in_list_p2p[m]
            
            if ss[0][0]==s[0][0]:
                for tt in ss[1:]:
                    p2p.append(tt[0])
                    
                for i in range(len(s)-len(ss)):
                    p2p.append(p2p[len(p2p)-1])
                m+=1
            else:
                for t in s[1:]:
                    p2p.append(p2p[len(p2p)-1])
        print (len(p2p))
        print (len(pureweb))
        
        fig, ax = plt.subplots()   
        n = len(pureweb)  
        x = np.arange(len(pureweb))
        ax.plot(x[(25*n)/30:(26*n)/30],p2p[(25*n)/30:(26*n)/30],color='g',marker='+',linestyle='None',label='Local peers (via PICN)')
        ax.set_yscale('log')
        plt.savefig(self.out_path + 'size_p2p.pdf',dpi=5) 
        fig, ax = plt.subplots() 
        ax.plot(x[(25*n)/30:(26*n)/30],pureweb[(25*n)/30:(26*n)/30],color='k',marker='.',linestyle='None',label='main web servers')
        ax.set_yscale('log')
        plt.savefig(self.out_path + 'size.pdf',dpi=5)        
        
            
    def plot_size_avgtime_detail(self):
        listout = self.loadlist(self.out_path + 'p2p_local_list')
        p2p_size_time = defaultdict()
        for r in listout:
            p2p_size_time.setdefault(r['len'], [[r['latency'],r['overhead']]]).append([r['latency'],r['overhead']])
        
        listout = []
        listout = self.loadlist(self.out_path + 'pure_web')
        pure_web_size_time = defaultdict()
        for r in listout:
            pure_web_size_time.setdefault(r['len'], [[r['latency'],r['overhead']]]).append([r['latency'],r['overhead']])
        listout = []            
        
        avg_size_p2p,maxsize_p2p,in_list_p2p = self.sortDict_2list(p2p_size_time)
        avg_size_pure_web,maxsize_pure_web,in_list_pure_web = self.sortDict_2list(pure_web_size_time)
        f= open('p2p_size','w')
        for l in in_list_p2p:
            print (l,file=f)
            print ('\n\n',file=f)
        f.close()
        f= open('pureweb_size','w')
        for l in in_list_pure_web:
            print (l,file=f)
            print ('\n\n',file=f)
        f.close()
        p2p = dict()       
        pureweb = dict()   
        m = 0
        print (maxsize_p2p)
        print (maxsize_pure_web)
        pre = 0
        for s in in_list_pure_web:
            if s[0][0]>maxsize_p2p:
                print('*')
                break
            newlist=[]
            for t in s[1:]:
                newlist.append(t[0])
            pureweb.setdefault(round(s[0][0]/float(8000),2),sum(newlist)/float(len(newlist)*1000000))
            ss = in_list_p2p[m]
            
            if ss[0][0]==s[0][0]:
                newlist=[]
                for tt in ss[1:]:
                    newlist.append(tt[0])
                pre = sum(newlist)/float(len(newlist)*1000000)
                p2p.setdefault(round(s[0][0]/float(8000),2),pre)    
                m+=1
            else:
                p2p.setdefault(round(s[0][0]/float(8000),2),pre)    
        print (len(p2p))
        print (len(pureweb))
        
        x = np.arange(len(p2p.keys()))        
        y_pureweb = np.array(pureweb.values()).astype(np.float)
        y_pureweb_mask = np.isfinite(y_pureweb)
        
        y_p2p = np.array(p2p.values()).astype(np.float)
        y_p2p_mask = np.isfinite(y_p2p)
        
        
        #print 'plotting url_speed...'
        fig, ax = plt.subplots()
        diag_p2p = ax.plot(x[y_p2p_mask],y_p2p[y_p2p_mask],color='g',linestyle='--',linewidth = 3,label='local_p2p')
        #diag_pureweb = ax.plot(x[y_pureweb_mask],y_pureweb[y_pureweb_mask],color='k',marker='x',linewidth = 3,label='original web server')
        ax.set_yscale('log')
        ax.set_ylabel('Latency(s)')
        ax.set_xlabel('content size(KByte)')
        ax.legend([diag_p2p[0]],['local peer'],loc=0,fontsize=18) 
        #ax.legend((diag_p2p[0],diag_pureweb[0]),('local peer','pure web server'),loc=0,fontsize=18) 
        fig.savefig(self.out_path + 'size_avgtime_detail.pdf',format='PDF',dpi=5)
        plt.show(block=False)        
        
    
if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("-o", "--out_path", dest="out_path",
                      help="output path for diagrams")
    
    parser.add_option("-s", "--proxyserver", dest="proxy",
                      help="whether compare with proxy or not (yes,no)")
    (options, args) = parser.parse_args()
    if options.proxy:
        if options.proxy=='yes':
            proxy = True 
        else:
            proxy = False
    else:
        proxy==False
    
    res = Results(options.out_path)
    res.calculate_speed_cdf(proxy)
    res.plot_size_time(proxy)
#    proxy_hit, proxy_miss, picn_p2p, picn_rp2p, picn_miss, pure_web = res.calculate_speed_cdf(proxy)
#    res.plot_cdf_picn(picn_p2p,picn_rp2p,picn_miss,pure_web)    
#    if proxy:
#        if proxy_hit[0]!=None:
#            res.plot_cdf_proxy_picn(proxy_hit, proxy_miss, picn_p2p, picn_rp2p, picn_miss,pure_web)
     #   res.plot_cdf_proxy(proxy_hit,proxy_miss)
        
