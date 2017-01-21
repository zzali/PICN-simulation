# PICN_simulation
# written by Zeinab Zali 
# April 2016

#requirements:
python packages

#Instructions for running the simulation:
- change the directory to PICN_simulation directory
- execute command:
  $ python SimulatorExecution.py -p tracefiles_folder -c cache_policy -a availability_probability -r request_rate
  
  please replace the input arguments with proper values as below:
  
  + tracefiles_folder: the folder path containing input trace files. All the trace files of UC Berkeley Home IP web traces                            are in the UC_Berkeley_traces folder in PICN_simulation folder. The names of these files are started                            with trace_detail (these are achieved with executing command showtrace form UCB-HOME-IP-tools). The                            trace files 1 to 4 are the main trace files from UCB-HOME-IP and trace_detail_5 is the sample trace                            detail of 4 hour snippet of trace data. You should place every trace file which you want to execute                            simulation for it, in the tracefiles_folder. The simulation is executed for aggregated traffic of all                          the trace files in this folder. 
  
  + cache_policy: one of these policies: fully_redundant, no_redundant or popularity_based
  
  + availability_probability: The availability probability of clients in percent
  + request_rate: Request rate for regenerating the traffic of requests in trace files in microseconds
  
  example execution command: 
  $ python SimulatorExecution.py -p UC_Berkeley_traces -c fully_redundant -a 90 -r 0.0005
  
#Output files:
All the output files are placed in the output folder in PICN_simulation folder. These files include all output diagrams and also info.txt file. The info file contains the simulation input and results statistics.
  
  
  


