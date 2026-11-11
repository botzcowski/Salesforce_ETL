from simple_salesforce import Salesforce, SalesforceLogin
from pandas import DataFrame, read_csv, set_option
from pprint import pprint as pp
from argparse import ArgumentParser
from datetime import date, datetime
from pathlib import Path

from sf_utility import writeToLog, utcNow, saveCDCDate, getMaxEndDate, querySf
from mongodb_utility import mongodb
from mssqldb_utility import mssqldb

import sys, json
import datetime

# Set pandas options
set_option('display.max_colwidth', 0)

#*************************************************************************************
# Get parameter from arguments
#*************************************************************************************
parser = ArgumentParser(description="Extract Salesforce object to csv file")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-datadir", help="The directory to store the output csv files")
parser.add_argument("-objdir", help="The directory that contains text files for each object's fields that are to be extracted")
parser.add_argument("-objname", help="The Salesforce object name")
parser.add_argument("-objfields", help="The Salesforce object field names")
parser.add_argument("-cdcdate", help="The datetime of last extraction run and the starting date of the systemmodstamp query filter")
parser.add_argument("-cdcfield", help="Mode=CreatedDate to filter by record creation date, Mode=SystemModStamp to filter by record modified date")
parser.add_argument("-logfile", help="The path to the log file")
args = parser.parse_args()

# Set parameter values to varibles
org =  args.org
objname = args.objname
objdir = args.objdir
objfields = args.objfields
cdcdate = args.cdcdate
cdcfield = args.cdcfield
logfile = args.logfile

#Create a subdirectory with today's date
#datapath = Path(args.datadir) / date.today().isoformat() 
datapath = Path(args.datadir) / cdcdate[0:10]
try:
  datapath.mkdir(parents=True) 
except FileExistsError:
  pass

nextStartDate = utcNow()
writeToLog(logfile, 'Saving cdc for next ' + objname + ' extraction run ' + nextStartDate)

writeToLog(logfile, 'Starting data Extraction for ' + objname)

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
maxdayrange = config['max_day_range'] 
sfsystemfields = config['extract_add_sf_system_fields'] 
sf_api_version = config['sf_api_version']
db = config['db'] 

#*************************************************************************************
# Get db connection info
#*************************************************************************************
if db!='':
    dbconfig = json.load(open('db_config_' + org + '.json')) 
    host = dbconfig['host']
    database = dbconfig['dbname']
    username = dbconfig['username']
    password = dbconfig['password']

# Connect to db
if db=='mongo':
    dbo = mongodb(host, database, username, password)
    if dbo.connectToDB():
        writeToLog(logfile, 'Connection to db sucessful')
    else:    
        writeToLog(logfile, 'Connection to db failed with error '+dbo.get_message())
if db=='mssql':
    dbo = mssqldb(host, database, objname, username, password)
    if dbo.connectToDB():
        writeToLog(logfile, 'Connection to db sucessful')
    else:    
        writeToLog(logfile, 'Connection to db failed with error '+dbo.get_message())

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

try:
    if consumer_key:
        sf = Salesforce(consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain, version=sf_api_version)
    else:
        sf = Salesforce(username=username, password=password, security_token=token, domain=domain, version=sf_api_version)
except Exception as e:
    writeToLog(logfile, 'Login to Salesforce failed ' + str(e))
    exit()


#*************************************************************************************
# Contruct Salesforce SOQL statement
#*************************************************************************************
if sfsystemfields:
    if objname.find('history') > 0:
        standardfields = ',CreatedById,CreatedDate,SystemModstamp'
    elif objname.find('userrole') >= 0:    
        standardfields = ',SystemModstamp'
    else:
        standardfields = ',CreatedById,CreatedDate,LastModifiedById,LastModifiedDate,SystemModstamp'
    SOQL = 'SELECT '+objfields+standardfields+' FROM '+objname+' WHERE '+cdcfield+' >= '+cdcdate
else:
    SOQL = 'SELECT '+objfields+' FROM '+objname+' WHERE '+cdcfield+' >= '+cdcdate

# Check if we need to add an end date filter - when date range exceeds the cap on the range of days of modified record to extract.
enddate = getMaxEndDate(cdcdate, maxdayrange)
if enddate != '':
    SOQL = SOQL + ' AND '+cdcfield+' <= '+ enddate
    nextStartDate = enddate

writeToLog(logfile, 'Date Extraction for ' + objname + ' with query: "' + SOQL + '"')

outputfile = datapath / (objname+'.csv')

#*************************************************************************************
#TODO: remove this debug
#*************************************************************************************
#sys.exit(0)

#*************************************************************************************
# Call Salesforce Web API to query data, save results to csv and db
#*************************************************************************************
try:   
    outkeys, outdata = querySf(sf, SOQL, objname, logfile)
    # Write data to csv
    DataFrame(outdata).to_csv(outputfile, header=True, index=False, encoding='utf-8')

    # Save next query "from date" filter to file
    cdcfile = Path(objdir) / (objname+'_last_run.txt')
    saveCDCDate(cdcfile, nextStartDate)

    if db=='mongo':
        # Bulk write to mongo db
        if dbo.bulkSaveRecords(objname, outkeys, outdata):
            writeToLog(logfile, 'Bulk Write to db successful: ' + dbo.get_message())
        else:
            writeToLog(logfile, 'Bulk Write to db failed: ' + dbo.get_message())
    if db=='mssql':
        # Bulk insert to mssql db
        if dbo.bulkSaveRecords(outputfile):
            writeToLog(logfile, 'Bulk Write to db successful: ' + dbo.get_message())
        else:
            writeToLog(logfile, 'Bulk Write to db failed: ' + dbo.get_message())
        dbo.disconnectFromDB()    

    writeToLog(logfile, 'Data Extraction for ' + objname + ' completed')    
except Exception as e:
    writeToLog(logfile, 'Data Extraction for ' + objname + ' error: ' + str(e))

   