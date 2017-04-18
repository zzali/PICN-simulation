# PICN-simulation
 written by Zeinab Zali (z.zali@ec.iut.ac.ir)
 April 2016

# requirements
python packages

# Input files

- Berkeley trace files
you can download the trace files from http://ita.ee.lbl.gov/html/contrib/UCB.home-IP-HTTP.html. 
After downloading the trace compressed files, please generate The trace detail information using showtrace tool available in ftp://ita.ee.lbl.gov/software/UCB-home-IP.tools.tar.gz (gzcat <tracefile> | showtrace > trace_detail_file). 
Then put all the files in a single folder.

- IRCache trace files
We use IRCache 2007 trace files : http://imdc.datcat.org/collection/1-01J0-5=IRCache+traces+for+DITL+January,+2007. But unfortunately the download link is no more available. So please contact me at z.zali@ec.iut.ac.ir if you want the files.
Then put all the files in a seperate folder than Berkeley trace files folder.

- Preprocesing the trace files
To generate the input files for simulation, execute:

  $python EventsProcessor.py -D dataset_name -p tracefiles_folder_path -d day

day is only necessary for IRCache trace files which can be 9 or 10

# Instructions for running the simulation
- change the directory to PICN_simulation directory
- execute command:

    $ python SimulatorExecution.py -D dataset -d day -p tracefiles_folder -c cache_policy -a availability_probability -m cache_size -s central_proxy
  
  please replace the input arguments with proper values as below:
  + Dataset: Berkeley or IRCache
  + day: it is necessary for IRCache trace files which can be 9 or 10
  + tracefiles_folder: the folder path containing input trace files. This folder should contain only the trace detail files                          which are generated from original trace files. You should place every trace file which you want to                            execute simulation for it in the tracefiles_folder. The simulation is executed for aggregated traffic                        of all the trace files in this folder. If you want to execute a simulation for a small trace file to                          evaluate the simulation code, use only the small 4 hour snippet of trace data available in UCB-Home-IP                        page. we already have put this sample file in UC_Berkeley_traces folder in PICN_simulation folder.
  
  + cache_policy: one of these policies: fully_redundant, no_redundant or popularity_based
  + availability_probability: The availability probability of clients in percent
  + cache_size: size of cache on each single client (KB)
  + proxy: yes or not. If it is yes a simulation for central proxy is also executed for Berkeley trace files or the results              will be compared with IRCache proxies for IRCache trace files
  
  example execution command: 
  
    $ python SimulatorExecution.py -p UC_Berkeley_traces -c fully_redundant -a 90 -d 9
  
# Output files
All the output files are placed in the output folder in PICN-simulation folder. These files include all output diagrams and also info.txt file. The info file contains the simulation input and results statistics.
  
  
  


