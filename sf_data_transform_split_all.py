from simple_salesforce import Salesforce
from pandas import DataFrame
import pandas as pd
from sf_utility import writeToLog
from datetime import date
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import os, json, sys, io

parser = ArgumentParser(description="Spli transform data into csv files for DML operations")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-obj", help="The master object name")
parser.add_argument("-getref", help="Retreive the refrence data")
parser.add_argument("-datadir", help="The directory to containing the input csv files")
parser.add_argument("-stagedir", help="The directory to store the csv files of the transformed data")
parser.add_argument("-logdir", help="The directory that contains the log files")
args = parser.parse_args()

# Get the directory paths 
org =  args.org
master_object = args.obj
datadir = args.datadir
stagedir = args.stagedir
logdir = args.logdir
getref = args.getref.lower() in ['true', 't', 'yes', 'y', '1']

# Create a log directory
logdir = Path(args.logdir) / date.today().isoformat() 
try:
  logdir.mkdir(parents=True)
except FileExistsError:
  pass

# Create a log file
logfile = Path(args.logdir) / date.today().isoformat() / 'split_log.txt'

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
targetObjects = config['target_objects']
sf_api_version = config['sf_api_version']

res = [sub for sub in targetObjects if sub['target_object']['name'] == master_object]
res = res[0] if res else None
if res == None:
    writeToLog(logfile, 'Unable to get target object from configurationm for ' + master_object)
    exit()
else:  
    source_object = res['source_object']['name'] 
    source_id_field  = res['target_object']['source_id_field'] 
    related_objects = res['target_object']['related_objects'] 

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

#Create the output subdirectory
datapath = Path(args.datadir)
try:
  datapath.mkdir(parents=True) 
except FileExistsError:
  pass

writeToLog(logfile, 'Starting Transformation Split for data files')

outputfile = datapath / (source_object+'_'+master_object+'.csv')

if getref:
    #*************************************************************************************
    # Call Salesforce Web API to query reference data, save results to csv
    #*************************************************************************************    
    try:
        if consumer_key:
            sf = Salesforce(consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain, version=sf_api_version)
        else:
            sf = Salesforce(username=username, password=password, security_token=token, domain=domain, version=sf_api_version)
    except Exception as e:
        writeToLog(logfile, 'Login to Salesforce failed ' + str(e))
        exit()

    dfs = []

    try:   
        # Get source refernce ids sorted to facilate faster lookup.
        SOQL = 'SELECT Id, '+source_id_field+' FROM '+master_object + ' WHERE '+source_id_field+'!=\'\'' + 'ORDER BY '+source_id_field

        results = sf.bulk2.__getattr__(master_object).query(SOQL, column_delimiter="COMMA", line_ending="LF")
        for idx, data in enumerate(results):
            df_batch = pd.read_csv(io.StringIO(data))
            dfs.append(df_batch)

        combined_df = pd.concat(dfs, ignore_index=True)
        DataFrame(combined_df).to_csv(outputfile, header=True, index=False, encoding='utf-8')

        writeToLog(logfile, 'Reference data extraction from ' + master_object + ' completed')    
    except Exception as e:
        writeToLog(logfile, 'Reference data extraction from ' + master_object + ' error: ' + str(e))

processes = []
# Get all staged data files to execute tranformation.
stagedir_path = Path(stagedir)
subdirs = [item for item in stagedir_path.rglob("*") if item.is_dir()]

for idx, subdir in enumerate(subdirs):
    writeToLog(logfile, 'Process files in ' + str(subdir) + ' for splitting')

    # Compose python execution string 
    execution_string = 'python3 sf_data_transform_split.py -org ' + org + ' -obj ' + master_object + ' -datadir ' + str(datadir) + ' -stagedir ' + str(subdir) + ' -logfile ' + str(logfile)

    processes.append(subprocess.Popen(["start", "/wait", "cmd.exe", "/K", execution_string], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True))

