from simple_salesforce import Salesforce
from pandas import DataFrame, set_option
import pandas as pd
from argparse import ArgumentParser
from pathlib import Path

from sf_utility import writeToLog, isValidJSON, querySf
import os, sys, json, time, csv

# Set pandas options
set_option('display.max_colwidth', 0)

parser = ArgumentParser(description="Set the master record id in the related field value for this related object")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-obj", help="The master object name")
parser.add_argument("-robj", help="The related object name")
#parser.add_argument("-ref", help="The reference data file name")
parser.add_argument("-datadir", help="The directory to containing the reference data files")
parser.add_argument("-stagedir", help="The directory to store the csv files of the related object's data")
parser.add_argument("-logfile", help="The path to the log file")
args = parser.parse_args()

#Get parameters from arguments
org =  args.org
master_object = args.obj
related_object = args.robj
#refdata = args.ref
datadir = args.datadir
stagedir = args.stagedir
logfile = args.logfile

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
targetObjects = config['target_objects']
maxRecs = config['max_records_per_file']
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

res = [sub for sub in related_objects if sub['related_object'] == related_object]
res = res[0] if res else None
if res == None:
    writeToLog(logfile, 'Unable to get related object from configurationm for ' + related_object)
    exit()
else:  
    source_field = res['source_field']
    relationship_field = res['relationship_field']

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

#refdatapath = Path(args.datadir)
datapath = Path(args.stagedir)
#Create the output subdirectory
try:
  datapath.mkdir(parents=True) 
except FileExistsError:
  pass

#ref_file = refdatapath / (source_object + '_' + master_object+'.csv')
#outputfile = datapath / (related_object + '.csv')

writeToLog(logfile, 'Starting related data extract for ' + related_object)

try:
    if consumer_key:
        sf = Salesforce(consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain, version=sf_api_version)
    else:
        sf = Salesforce(username=username, password=password, security_token=token, domain=domain, version=sf_api_version)
except Exception as e:
    writeToLog(logfile, 'Login to Salesforce failed ' + str(e))
    exit()

#*************************************************************************************
# Call Salesforce Web API to query the related object's data, save results to csv
#*************************************************************************************
try:   
    SOQL = 'SELECT Id, '+source_field+', '+relationship_field+' FROM '+related_object+' WHERE '+source_field+'!=\'\' AND '+relationship_field+'=\'\' ORDER BY '+source_field
    #outkeys, outdata = querySf(sf, SOQL, related_object, logfile)
    #if len(outdata) > 0:
        # Write data to csv
    #    DataFrame(outdata).to_csv(outputfile, header=True, index=False, encoding='utf-8')
    results = sf.bulk2.__getattr__(related_object).query(SOQL, max_records=maxRecs, column_delimiter="COMMA", line_ending="LF")
    for idx, data in enumerate(results):
        subdir = related_object + '_chunk_' + str(idx)
        #Create the output subdirectory
        subdirpath = datapath / subdir
        try:
            subdirpath.mkdir(parents=True) 
        except FileExistsError:
            pass
        outputfile = subdirpath / (related_object + '.csv')
        with open(outputfile, 'w',  encoding='utf-8') as bos:
            bos.write(data)

    writeToLog(logfile, 'Related data extraction for ' + related_object + ' completed')    
except Exception as e:
    writeToLog(logfile, 'Related data extraction for ' + related_object + ' error: ' + str(e))
