from sf_utility import writeToLog 
from datetime import date
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import json

parser = ArgumentParser(description="Transform data in csv files")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-objdir", help="The directory that contains the field mapping files for each object's data that are to be transformed")
parser.add_argument("-datadir", help="The directory to containing the input csv files")
parser.add_argument("-stagedir", help="The directory to store the csv files of the transformed data")
parser.add_argument("-logdir", help="The directory that contains the log files")
args = parser.parse_args()

# Get the directory paths 
org =  args.org
objdir = args.objdir
datadir = args.datadir
stagedir = args.stagedir
logdir = args.logdir

#*************************************************************************************
# Get Salesforce connection info
#*************************************************************************************
login = json.load(open('login_' + org + '.json')) 
username = login['username'] 
password = login['password'] 
token = login['token']
consumer_key = login['consumer_key']
consumer_secret = login['consumer_secret']
domain = login['domain']

# Create a log directory
logdir = Path(args.logdir) / date.today().isoformat() 
try:
  logdir.mkdir(parents=True)
except FileExistsError:
  pass

# Create a log file
logfile = Path(args.logdir) / date.today().isoformat() / 'transform_log.txt'

writeToLog(logfile, 'Starting Transformation for data files')

processes = []
# Get all data files to execute tranformation.
datadir = Path(datadir)
datasubdirs = [item for item in datadir.rglob("*") if item.is_dir()]

for idx, subdir in enumerate(datasubdirs):
    writeToLog(logfile, 'Process files in ' + str(subdir) + ' for transformation')

    # Compose python execution string 
    execution_string = 'python3 sf_data_transform.py -org ' + org + ' -objdir ' + objdir + ' -datadir ' + str(subdir) + ' -stagedir ' + stagedir + ' -logfile ' + str(logfile)
    # Run python script to transform data files. 
    #os.system(execution_string)

    processes.append(subprocess.Popen(["start", "/wait", "cmd.exe", "/C", execution_string], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True))

