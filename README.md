# PICN_simulation
# written by Zeinab Zali 
# April 2016

#requirements:
python packages

#Input files:
you can download the trace files from http://ita.ee.lbl.gov/html/contrib/UCB.home-IP-HTTP.html. After downloading the trace compressed files, please generate The trace detail information using showtrace tool available in                         ftp://ita.ee.lbl.gov/software/UCB-home-IP.tools.tar.gz (gzcat <tracefile> | showtrace > trace_detail_file). Then place these files in a folder which is used in the execution and we explain about it in the next section.

#Instructions for running the simulation:
- change the directory to PICN_simulation directory
- execute command:
  $ python SimulatorExecution.py -p tracefiles_folder -c cache_policy -a availability_probability -r request_rate
  
  please replace the input arguments with proper values as below:
  
  + tracefiles_folder: the folder path containing input trace files. This folder should contain only the trace detail files                          which are generated from original trace files. You should place every trace file which you want to                            execute simulation for it in the tracefiles_folder. The simulation is executed for aggregated traffic                        of all the trace files in this folder. If you want to execute a simulation for a small trace file to                          evaluate the simulation code, use only the small 4 hour snippet of trace data available in UCB-Home-IP                        page. we already have put this sample file in UC_Berkeley_traces folder in PICN_simulation folder.
  
  + cache_policy: one of these policies: fully_redundant, no_redundant or popularity_based
  
  + availability_probability: The availability probability of clients in percent
  + request_rate: Request rate for regenerating the traffic of requests in trace files in microseconds
  
  example execution command: 
  $ python SimulatorExecution.py -p UC_Berkeley_traces -c fully_redundant -a 90 -r 0.0005
  
#Output files:
All the output files are placed in the output folder in PICN_simulation folder. These files include all output diagrams and also info.txt file. The info file contains the simulation input and results statistics.
  
  
  


