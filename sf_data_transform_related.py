from pandas import set_option
import pandas as pd
from argparse import ArgumentParser
from pathlib import Path

from sf_utility import writeToLog, getSortedFiles
import json, sys

def GetRelated(related_object, targetObjects, master_object):
    global source_object
    global source_id_field
    global source_field
    global relationship_field

    res = [sub for sub in targetObjects if sub['target_object']['name'] == master_object]
    res = res[0] if res else None
    if res == None:
        writeToLog(logfile, 'Unable to get target object from configuration for ' + master_object)
        exit()
    else:  
        source_object = res['source_object']['name'] 
        source_id_field  = res['target_object']['source_id_field'] 
        related_objects = res['target_object']['related_objects'] 

    res = [sub for sub in related_objects if sub['related_object'] == related_object]
    res = res[0] if res else None
    if res == None:
        writeToLog(logfile, 'Unable to get related object from configuration for ' + related_object)
        exit()
    else:  
        source_field = res['source_field']
        relationship_field = res['relationship_field']


# Set pandas options
set_option('display.max_colwidth', 0)

parser = ArgumentParser(description="Set the master record id in the related field value for this related object")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-obj", help="The master object name")
parser.add_argument("-datadir", help="The directory to containing the reference data files")
parser.add_argument("-stagedir", help="The directory with the csv files of the related object's data")
parser.add_argument("-logfile", help="The path to the log file")
args = parser.parse_args()

#Get parameters from arguments
org =  args.org
master_object = args.obj
datadir = args.datadir
stagedir = args.stagedir
logfile = args.logfile

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
targetObjects = config['target_objects']
maxRecs = config['max_records_per_file']
sf_api_version = config['sf_api_version']
refdatapath = Path(args.datadir)

# Get all data csv file in the input directory
files = getSortedFiles(stagedir)
relatedTypes = set()

for idx, datafile in enumerate(files):
    if datafile.endswith(".csv"):
        # Determine related object from file name
        related_object = Path(datafile).stem
        stage_file_path = Path(stagedir+'\\'+datafile)

        writeToLog(logfile, 'Starting relatonship field lookup for ' + related_object)

        if related_object not in relatedTypes:
            GetRelated(related_object, targetObjects, master_object)

            ref_file = refdatapath / (source_object + '_' + master_object+'.csv')
            # read reference file
            try:
                dfref = pd.read_csv(ref_file, encoding='utf-8')
            except Exception as e:
                writeToLog(logfile, 'Open reference lookup file error ' + str(e))
                exit()

            relatedTypes.add(related_object)

        # Read through related file records and get the related field value from the reference data file
        try:
            df = pd.read_csv(stage_file_path, dtype=str)
            for index, row in df.iterrows():
                # Find the row in the reference data file to locate the master record Id
                if row[source_field] != '':
                    # find the entry in the referece table where the source_id_field value (record id) = the value (record id) of the source lookup field for the given row
                    indexRef = dfref[dfref[source_id_field] == row[source_field]].index
                    if not indexRef.empty: 
                        #writeToLog(logfile, 'Reference file index ' + str(indexRef))
                        # Set related record's relationship field with the master record's Id
                        df.loc[index, relationship_field] = dfref.loc[indexRef.values.astype(int)[0], 'Id']
                        sys.stdout.write(f"{index+1} records processed \r")
                        sys.stdout.flush()
            # Save the updates       
            df.to_csv(stage_file_path, index=False)    
            writeToLog(logfile, 'Completed relatonship field lookup on file ' + str(datafile))

        except FileNotFoundError:
            writeToLog(logfile, 'File ' + str(datafile) + ' not found.')
        except Exception as e:
            writeToLog(logfile, 'Error on relatonship lookup in file ' + str(datafile) + ' ' + str(e))

