from simple_salesforce import Salesforce
from sf_utility import writeToLog, isValidJSON, getFieldNames
from datetime import date, datetime
from argparse import ArgumentParser
from pathlib import Path
import os

#*************************************************************************************
# Get parameter from arguments
#*************************************************************************************
parser = ArgumentParser(description="Get object fields")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-objdir", help="The directory that contains text files for each object's fields that are to be extracted")
parser.add_argument("-datadir", help="The directory to store the output csv files")
parser.add_argument("-logdir", help="The directory that contains the log files")
parser.add_argument("-cdcfield", help="Mode=CreatedDate to filter by record creation date, Mode=SystemModStamp to filter by record modified date")
args = parser.parse_args()

# Get the directory paths 
org =  args.org
objdir = args.objdir
datadir = args.datadir
logdir = args.logdir
cdcfield = args.cdcfield

# Create a log directory
logdir = Path(args.logdir) / date.today().isoformat() 
try:
  logdir.mkdir(parents=True)
except FileExistsError:
  pass

# Create a log file
logfile = Path(args.logdir) / date.today().isoformat() / 'extraction_log.txt'

writeToLog(logfile, 'Starting Extractions for all objects')

# Get all files in the directory, each pair of files represents 1 Salesforce object.
paths = Path(objdir).glob('**/*.txt')
for path in paths:
    # Convert object to string
    path_str = str(path)
    file_name = Path(path_str).stem    
    if (file_name.find('_last_run') == -1):
        # Any text file in the directory is not the CDC file then it's assumed to be the configuration file containing the field names 
        # Get the Salesforce object field api names from the configuration file, or from the file specified in the json string.
        with open(path_str, 'r') as file:
             sf_fields = file.read().replace('\n', '')
             # When the configuration file is a JSON string the field names are in a mapping sheet located by the JSON attributes
             if (isValidJSON(sf_fields)):
                 sf_fields = getFieldNames(sf_fields, objdir, 'source')

        date_file = path_str.replace('.txt', '_last_run.txt')     
        sf_objname = file_name

        # Get cdc dates from configuration file
        with open(date_file, 'r') as file:
             last_run_date = file.read().replace('\n', '')

        writeToLog(logfile, 'Invoking '+ org + ' ' + sf_objname + ' extraction script for data created & modified after ' + last_run_date)

        # Compose python execution string 
        execution_string = 'python3 sf_data_extract.py -org ' + org + ' -objdir ' + objdir + ' -datadir ' + datadir + ' -logfile ' + str(logfile) + ' -objname ' + sf_objname + ' -cdcfield ' + cdcfield + ' -cdcdate ' + last_run_date + ' -objfields "' + sf_fields + '"' 
        # Run python script to extract data for the given object. 
        os.system(execution_string)

   
