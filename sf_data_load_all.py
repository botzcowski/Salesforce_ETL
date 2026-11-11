from sf_utility import writeToLog
from datetime import date, datetime
from argparse import ArgumentParser
from pathlib import Path
import os, sys, json

parser = ArgumentParser(description="Upsert data from csv files to Salesforce objects")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-mode", help="update/upsert/insert")
parser.add_argument("-stagedir", help="The directory that stores the csv files to be loaded")
parser.add_argument("-logdir", help="The directory that contains the log files")
args = parser.parse_args()

# Get the directory paths 
org =  args.org
stagedir = args.stagedir
logdir = args.logdir
mode = args.mode

# Create a log directory
logdir = Path(args.logdir) / date.today().isoformat() 
try:
  logdir.mkdir(parents=True)
except FileExistsError:
  pass

# Create a log file
logfile = Path(args.logdir) / date.today().isoformat() / 'load_log.txt'

writeToLog(logfile, 'Starting load for data files')

# Load data files at the current directory. 
execution_string = 'python3 sf_data_load.py -org ' + org + ' -mode ' + mode + ' -stagedir ' + str(stagedir) + ' -logdir ' + str(logdir) + ' -logfile '+ str(logfile)
os.system(execution_string)

# Load data files in each subdirectory.
stagedir = Path(stagedir)
stagesubdirs = [item for item in stagedir.rglob("*") if item.is_dir()]
for subdir in stagesubdirs:
    writeToLog(logfile, 'Process files in ' + str(subdir) + ' for loading')

    # Compose python execution string 
    execution_string = 'python3 sf_data_load.py -org ' + org + ' -mode ' + mode + ' -stagedir ' + str(subdir) + ' -logdir ' + str(logdir) + ' -logfile '+ str(logfile)
    # Run script to load data files in the directory. 
    os.system(execution_string)