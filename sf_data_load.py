from simple_salesforce import Salesforce, SalesforceMalformedRequest
from argparse import ArgumentParser
from pathlib import Path
from sf_utility import writeToLog, getSortedFiles, getSfResults
import json

parser = ArgumentParser(description="Upsert/insert data from this csv files to Salesforce object")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-mode", help="update/upsert/insert")
parser.add_argument("-stagedir", help="The directory that stores the csv files to be loaded")
parser.add_argument("-logdir", help="The log directory")
parser.add_argument("-logfile", help="The path to the log file")
args = parser.parse_args()

# Get parameters from arguments
org =  args.org
stagedir = args.stagedir
logdir = args.logdir
logfile = args.logfile
mode = args.mode

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
targetObjects = config['target_objects']
sf_api_version = config['sf_api_version']

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

# Connect to Salesforce
try:
    if consumer_key:
        sf = Salesforce(consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain, version=sf_api_version)
    else:
        sf = Salesforce(username=username, password=password, security_token=token, domain=domain, version=sf_api_version)
except Exception as e:
    writeToLog(logfile, 'Login to Salesforce failed ' + str(e))
    exit()

# Get all data csv file in the input directory
files = getSortedFiles(stagedir)

for idx, datafile in enumerate(files):
    if datafile.endswith(".csv"):
        file_name = str(datafile)
        stage_file_path = Path(stagedir+'\\'+file_name)
        sf_object_name = Path(file_name).stem

        if mode == 'upsert': 
            res = [sub for sub in targetObjects if sub['source_object']['name'] == sf_object_name]
            res = res[0] if res else None
            if res == None:
                writeToLog(logfile, 'Unable to get target object & external id from configuration for ' + sf_object_name)
                exit()
            else:  
                external_id_field = res['external_id_field']
                target_object = res['target_object']['name']  

        #*************************************************************************************
        #TODO: remove this debug
        #*************************************************************************************
        #sys.exit(0)

        writeToLog(logfile, 'Starting '+mode+' on file ' + str(stage_file_path))

        # Perform bulk operations 
        try:
            object_name = sf_object_name

            match mode:
                case 'insert':
                    results = sf.bulk2.__getattr__(object_name).insert(csv_file=stage_file_path)
                case 'update':
                    results = sf.bulk2.__getattr__(object_name).update(csv_file=stage_file_path)
                case 'upsert':
                    object_name = target_object
                    results = sf.bulk2.__getattr__(object_name).upsert(csv_file=stage_file_path, external_id_field=external_id_field)

            for idx, result in enumerate(results):
                writeToLog(logfile, 'Bulk '+mode+' on file ' + str(stage_file_path) + ' processed: ' + str(result['numberRecordsProcessed']) + ' failed: ' + str(result['numberRecordsFailed']))
                getSfResults(sf, result['job_id'], object_name, logdir)

        except SalesforceMalformedRequest as e:
            writeToLog(logfile, 'Bulk '+mode+' on file ' + str(stage_file_path) + ' request failed '+str(e))
        except Exception as e:
            writeToLog(logfile, 'Bulk '+mode+' on file ' + str(stage_file_path) + ' failed '+str(e))
