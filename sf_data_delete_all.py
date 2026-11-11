from sf_utility import writeToLog
from datetime import date, datetime
from argparse import ArgumentParser
from pathlib import Path
import os, sys, json

parser = ArgumentParser(description="Delete records from Salesforce objects using ids from csv files")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-stagedir", help="The directory that stores the csv files to be deleted")
parser.add_argument("-logdir", help="The directory that contains the log files")
args = parser.parse_args()

# Get the directory paths 
org =  args.org
stagedir = args.stagedir
logdir = args.logdir

# Create a log directory
logdir = Path(args.logdir) / date.today().isoformat() 
try:
  logdir.mkdir(parents=True)
except FileExistsError:
  pass

# Create a log file
logfile = Path(args.logdir) / date.today().isoformat() / 'delete_log.txt'

writeToLog(logfile, 'Starting deletion')

# Get all data files to execute delete.
stagedir = Path(stagedir)
stagesubdirs = [item for item in stagedir.rglob("*") if item.is_dir()]
for subdir in stagesubdirs:
    writeToLog(logfile, 'Process files in ' + str(subdir) + ' for deletion')

    # Compose python execution string 
    execution_string = 'python3 sf_data_delete.py -org ' + org + ' -stagedir ' + str(subdir) + ' -logdir ' + str(logdir) + ' -logfile '+ str(logfile)
    # Run python script to delete data. 
    os.system(execution_string)