# -*- coding: utf-8 -*-
from __future__ import print_function
import os 
from collections import defaultdict
from optparse import OptionParser
import random
import numpy as np
import matplotlib.pyplot as plt
import math
    
def getKey(req):
    return req['timestamp']
        
def getKey2(item):
    return item[1]
    
def plot_size_dstribution(times,name):
        rate = []
        interval = 30*60*1000
        i = 0  
#        print('plot rate')
#        print('len times',len(times))
#        print('time[0]',times[0])
        while i <len(times)-1: 
            preTime = times[i]
#            print('preTime',preTime)
            i = i + 1
            event_num = 1
            while i<len(times) and times[i]-preTime<interval:
                event_num = event_num + 1
                i+=1
#            print ('i ',i)    
            rate.append( event_num / float(interval))
#            print('times[i-1]-preTime',times[i-1]-preTime)
#            print('preTime',preTime)
#            print('times[i-1]',times[i-1])
#            print(event_num / float(interval))
        x = np.arange(len(rate))
        plt.plot(x,rate,color='r',marker='.',linewidth = 1,label='request rates')
        plt.xlabel('Time',fontsize=20)
        plt.ylabel('request rate',fontsize=20)
        plt.savefig(name,format='PDF',dpi=5)
        plt.clf()
       
def generate_ircache_events_file(path, day,alexa_rtt_bw):
    #remove NATs
    clients = defaultdict()
    NATs = defaultdict()
    nats_num = 10
    for filename in os.listdir(path+'/trace_'+day+'/'):
        print('reading ',filename)
        f = open(path+'/trace_'+day+'/' + filename)
        filekey = filename[0:2]
        client_address_freq = defaultdict() #frequency of requests for each client address
        clients.setdefault(filekey,set())
        NATs.setdefault(filekey,[])
        ## Read the first line 
        line = f.readline()
        while line:
            fields = line.split(" ")
            client = fields[2]
            provider= fields[3]
            clients[filekey].add(client)
            client_address_freq.setdefault(client,0)
            client_address_freq[client] += 1
            line = f.readline()
        maxx = 0
        host = ''
        for i in range(nats_num):
            for c in client_address_freq.keys():
                if client_address_freq[c]>maxx:
                    maxx = client_address_freq[c]
                    host = c
            NATs[filekey].append(host)
            client_address_freq.pop(host)
            maxx=0
       
    #read and extrace events
    max_size = 0
    size_sum = 0 
    eventList = []
    serversIP = []
    if not os.path.exists(path + '/events_dir_' + day + '/' ):
        os.makedirs(path + '/events_dir_' + day + '/')
    total_num_req = 0
    supported = 0
    url_cnt = 0
    timestamps = []
    urls = defaultdict()
    for filename in os.listdir(path+'/trace_'+day+'/'):
        f = open(path + '/trace_' + day+'/'+ filename)
        filekey = filename[0:2]
        clients_noNATs = list(clients[filekey].difference(set(NATs[filekey])))
        clients_noNATs_len = len(clients_noNATs)-1
        line = f.readline()        
        while line:
            fields = line.rstrip().split(" ")
            #if the request is not GET request deny it
            if len(fields)>=10 and fields[5]=='GET':
                responseLen = int(fields[4]) #number of bytes in http content without Eth,IP or TCP headers overhead
                if responseLen>0:
                    total_num_req +=1
                    responseTime = int(fields[1])
                    cip = fields[2]
                    sip = fields[8].split("/")[1]
                    tmp = fields[0].split(".")
                    timestamp = int(tmp[0])*1000+int(tmp[1])
                    timestamp = timestamp - responseTime
                    client_address_freq.setdefault(cip,0)
                    client_address_freq[cip] += 1
                    ctype = fields[9]
                    provider = fields[3]
                    url = fields[6]
                    if ctype.count("video")>0 or ctype.count("image")>0 or url.count("swf")>0:
                        isSupported = True
                        supported = supported + 1
                    else:
                        isSupported = False
                    url_cnt +=1
                    url_ID = urls.setdefault(url,url_cnt)
                    if provider.startswith('TCP_MISS/200') or provider.startswith('TCP_HIT/200') or provider.startswith('TCP_MEM_HIT/200'):
                        rand = random.randint(0,alexa_num)
                        rtt = alexa_rtt_bw[rand][0]  
                        bw = alexa_rtt_bw[rand][1]                                    
                    else: 
                        line = f.readline()
                        continue
                    if cip in NATs[filekey]:
                        cip = clients_noNATs[random.randint(0,clients_noNATs_len)]
                    if max_size<responseLen:
                        max_size = responseLen
                    size_sum = size_sum + responseLen
                    url_ID = str(url_ID) + '_' + str(responseLen)
                    timestamps.append(timestamp)
                    eventList.append({'URL':url_ID,'timestamp':timestamp,'rtt':rtt,'bw':bw,'latency':responseTime
                            ,'clientIP':cip,'serverIP':sip,'len':responseLen,'proxy_provider':provider,'isSupported':isSupported})
    
            line = f.readline()
        f.close()
        f = open(path + '/events_dir_'+day +'/clients_'+filekey,'w')
        for c in clients_noNATs:
            print(c,file=f)
        f.close()
    print('finished reading files')
    avg_size = size_sum/float(supported)
    eventList.sort(key=getKey) 
    fevents = open(path + '/events_dir_'+day +'/events.txt','w')  
    timestamps.sort()
    newTimes = timestamps
    i=0
    for e in eventList:
        print( str(newTimes[i]) + ' '+ str(e['URL']) + ' '+ str(e['len']) + ' ' + str(e['rtt']) + ' ' + str(e['bw']) + ' ' + str(e['latency']) + ' ' 
            + e['clientIP'] + ' ' + e['serverIP'] + ' ' + e['proxy_provider']+ ' ' + str(e['isSupported']),file=fevents)
        i += 1
   
    fevents.close()
    finfo = open(path + '/events_dir_'+day +'/events_info.txt','w')  
    print('IRCache 2007 trace file',file=finfo)    #contents number
    print(str(len(urls.keys())),file=finfo)    #contents number
    print(str(len(serversIP)),file=finfo)
    print(str(max_size),file=finfo)    #
    print(str(avg_size),file=finfo)    #            
    print(str(len(eventList)),file=finfo) 
    print(str(supported),file=finfo) 
    finfo.close()    

    
def generate_Times(timestamps_len,rate_factor):
    new_t = []
    new_t.append(0)
    time = 0
    for i in range(timestamps_len-1):
        time = int(time + round((1/rate_factor) * abs(math.log10(random.random()))))
        new_t.append(time)
    return new_t
        
def generate_berkeley_events_file(path, alexa_rtt_bw):
    print ("read log files...")
    size_sum = 0
    max_size = 0
    supported = 0
    
    timestamps = []
    urls = set()
    clientsIP = set()
    serversIP = set()
    #sort the files on date
    files = []
    for filename in os.listdir(path):
        if os.path.isdir(path+'/'+filename):
            continue
        f = open(path+ '/'+filename)
        ## Read the first line 
        line = f.readline()
        while line:
            fields = line.split(" ")
            if fields[13]=='GET':
                files.append({'filename':filename,'timestamp':fields[0]})
                break
            line = f.readline()
    files.sort(key=getKey)
    url_size= defaultdict()  
    eventList = []   
         
    for filename in files:
        f = open(path+'/'+ filename['filename'])
        print ('reading trace file ' + filename['filename'])
        ## Read the first line 
        line = f.readline()
        while line:
            #fields = [req_time,firstByteTime,LastByteTime,clientIP,ServerIP,clientHeader,
            #ServerHeader,IfModefinedSinceClientHeader,ExpiresServerHeader, LastModefiedServerHeader,responseHeaderLen,
            #responseDataLan,URLLen, GET, URLValue, HTTP/1.0]
            fields = line.rstrip().split(" ")
            #if the request is not GET request deny it
            if len(fields)>=15 and fields[13]=='GET':
                #compute response time in microseconds
                #original_responseLen = (int(fields[11]) + int(fields[10]))*8
                #responseLen = self.generate_size(int(fields[10]),int(fields[11]),self.distribution)
                responseLen = (int(fields[10])+int(fields[11]))
                if responseLen>0:
                    t = fields[0].split(":")
                    start_dt = int(t[0])*1000000+int(t[1])
                    t = fields[2].split(":")
                    end_dt = int(t[0])*1000000+int(t[1])
#                    t = fields[1].split(":")
#                    first_byte = int(t[0])*1000000+int(t[1])
                    responseTime = (end_dt - start_dt)/1000
                    if responseTime==0:
                        responseTime = 1
                    cip = fields[3].split(":")[0]
                    sip = fields[4].split(":")[0]
                    timestamps.append(start_dt/1000)
                    clientsIP.add(cip)
                    serversIP.add(sip)
                    url = fields[14]
                    urls.add(url)
                    headLen = int(fields[10])
                    url_size.setdefault(url,responseLen)
                    if responseLen > url_size[url]:
                        url_size[url] = responseLen
                        
                    if url.count("gif")>0 or url.count("jpg")>0 or url.count("jpeg")>0 or url.count("mp4")>0 or url.count("mov")>0 or url.count("mp3")>0 or url.count("swf")>0 \
                        or url.count("GIF")>0 or url.count("JPG")>0 or url.count("JPEG")>0 or url.count("MP4")>0 or url.count("MOV")>0 or url.count("MP3")>0 or url.count("SWF")>0 \
                        or url.count("exe")>0 or url.count("PNG")>0 or url.count("zip")>0 or url.count("ZIP")>0 or url.count("tar")>0 or url.count("rar")>0 or url.count("TAR")>0 \
                        or url.count("RAR")>0 or url.count("tar.gz")>0:
                        
                        isSupported = True
                        if max_size<responseLen:
                            max_size = responseLen
                        size_sum = size_sum + responseLen
                        supported = supported + 1
                    else:
                        isSupported = False
                    rand = random.randint(0,alexa_num)
                    rtt = alexa_rtt_bw[rand][0]  
                    bw = alexa_rtt_bw[rand][1]    
                    eventList.append({'URL':url,'timestamp':start_dt,'rtt':rtt,'bw':bw, 'latency':responseTime,\
                            'speed':responseLen/float(responseTime),'clientIP':cip,'serverIP':sip,\
                            'len':responseLen,'headLen':headLen,'isSupported':isSupported})
                   
                
            line = f.readline()
            #print (line )
        #sort eventList on request timestamp
         
        
        f.close()
    #end of for
    print('finished reading files')
    eventsPath = path + '/events_dir'
    if not os.path.exists(eventsPath):
        os.makedirs(eventsPath)
    f = open(eventsPath+'/clients_berkeley','w')
    for c in clientsIP:
        print(c,file=f)
    f.close()
    avg_size = size_sum/float(supported)
    fevents = open(eventsPath+'/events.txt','w')  
    eventList.sort(key=getKey)     
    timestamps.sort()
    newTimes = timestamps
    i = 0
    urls_set = defaultdict()
    saved_traffic = 0
    tot_traffic = 0
    for e in eventList:
        urls_set.setdefault(e['URL'],0)
        if urls_set[e['URL']]>0:
            saved_traffic += url_size[e['URL']]
        urls_set[e['URL']] += 1
        tot_traffic += url_size[e['URL']]
        print( str(newTimes[i]) + ' '+ str(e['URL']) + ' '+ str(url_size[e['URL']]) + ' ' + str(e['rtt']) + ' ' + str(e['bw']) + ' ' + str(e['latency']) + ' ' 
            + e['clientIP'] + ' ' + e['serverIP'] + ' ' + 'None'+ ' ' + str(e['isSupported']),file=fevents)
        i += 1
    
    fevents.close()
    #print('saved external traffic: ' + str(saved_traffic/float(tot_traffic)))
    finfo = open(eventsPath + '/events_info.txt','w')  
    print('Berkeley 96 trace file',file=finfo)    #contents number
    print(str(len(urls)),file=finfo)    #contents number
    print(str(len(serversIP)),file=finfo)
    print(str(max_size),file=finfo)    #
    print(str(avg_size),file=finfo)    #            
    print(str(len(eventList)),file=finfo) 
    print(str(supported),file=finfo) 
    finfo.close()        

#######################################################################################
if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("-D", "--Dataset", dest="dataset",
                      help="dataset (IRCache,Berkeley)")  
    parser.add_option("-p", "--path", dest="traceFiles_path",
                      help="Path to trace files for generating request traffic")
    parser.add_option("-d", "--day", dest="day",
                      help="Trace day (9,10)")    
                    
    (options, args) = parser.parse_args()
    dataset = (options.dataset) if options.dataset else 'IRCache'
    path = (options.traceFiles_path) if options.traceFiles_path else 'Data/IRCache'
    day = options.day if options.day else '9'
        
    #read alexa sites rtt (to bereferenced for rtt of IRcache servers based on popularity)
    f = open('Alexa_sites_rtt_bw_SAVI')        
    alexa_rtt_bw = []
    line = f.readline().rstrip()
    while(line):
        alexa_rtt_bw.append([float(line.split()[1]), float(line.split()[2])])
        line = f.readline()
    alexa_num = len(alexa_rtt_bw)-1
    if dataset=='IRCache':
        generate_ircache_events_file(path, day,alexa_rtt_bw)
    else:
        generate_berkeley_events_file(path, alexa_rtt_bw)
    
    
 
####################################################################################### 
def compute_popularity(path, day):
    uri_server = defaultdict()
    servers_freq = defaultdict()
    servers_freq_list = defaultdict()
    popularity_class = defaultdict()
    req_num = 0
    clients = defaultdict()
    NATs = defaultdict()
    nats_num = 10
    ######reading servers and clients information
    for filename in os.listdir(path+'/trace_'+day+'/'):
        print('reading ',filename)
        f = open(path+'/trace_'+day+'/' + filename)
        filekey = filename[0:2]
        client_address_freq = defaultdict() #frequency of requests for each client address
        uri_server.setdefault(filekey,defaultdict())
        servers_freq.setdefault(filekey,defaultdict())
        servers_freq_list.setdefault(filekey,[])
        clients.setdefault(filekey,set())
        ## Read the first line 
        line = f.readline()
        while line:
            fields = line.split(" ")
            client = fields[2]
            provider= fields[3]
            uri = fields[6]
            server = fields[8].split('/')[1]
            clients[filekey].add(client)
            client_address_freq.setdefault(client,0)
            uri_server[filekey].setdefault(uri, server)
            client_address_freq[client] += 1
            if provider.count('TCP_MISS')>0 and server!='':
                if server=='-':
                    if uri in uri_server.keys():
                        servers_freq[filekey][uri_server[uri]] += 1
                        req_num += 1 
                else:
                    servers_freq[filekey].setdefault(server,0)
                    servers_freq[filekey][server] += 1 
                    req_num += 1
            elif provider.count('TCP_HIT')>0 or provider.count('TCP_MEM_HIT')>0:
                if uri in uri_server.keys():
                    servers_freq[filekey][uri_server[uri]] += 1
                    req_num += 1
            line = f.readline()
            NATs.setdefault(filekey,[])
            maxx = 0
            host = ''
        for i in range(nats_num):
            for c in client_address_freq.keys():
                if client_address_freq[c]>maxx:
                    maxx = client_address_freq[c]
                    host = c
            NATs[filekey].append(host)
            client_address_freq.pop(c)
            maxx=0
        #calculate servers popularity
        print('number of servers: ' , str(len(servers_freq[filekey].keys())))    
        for s in servers_freq[filekey].keys():
            servers_freq[filekey][s] = round(100000*servers_freq[filekey][s]/float(req_num),5)
        servers_freq_list[filekey] = [[key,servers_freq[filekey][key]] for key in servers_freq[filekey].keys()]
        servers_freq_list[filekey].sort(key=lambda pair: pair[1], reverse=True)
        popularity_class[filekey] = 0
        pop = servers_freq_list[filekey][0][1]
        for s in servers_freq_list[filekey]:
            print(s[0] + ': ' + str(s[1]))
            if s[1]<pop:
                popularity_class[filekey] += 1
                pop = s[1]
        print('number of popularity classes: ' + str(popularity_class[filekey]))
    servers_freq_list,_ = compute_popularity(path , day)
    servers_pop_class = defaultdict()   
    for trace in servers_freq_list.keys():
        tmp = servers_freq_list[trace][0]
        pop_class = 0
        servers_pop_class.setdefault(trace,[])
        for s in servers_freq_list[trace]:
            ss = []
            if s[1]==tmp:
                ss.append(s)
                continue
            r = int(tmp / s[1])
            ss.insert(0,r)
            servers_pop_class[trace].append(ss)
            pop_class += r
    return servers_freq_list, popularity_class
