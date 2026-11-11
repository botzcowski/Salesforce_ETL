from pandas import set_option
from argparse import ArgumentParser
from pathlib import Path

from sf_utility import writeToLog, isValidJSON, getSortedFiles, getFieldNames
import os, sys, json, csv

def TransformData(source, transform):
    targetValue = '*No Data*'

    match transform:
        case 'ignore':
            pass
        case 'copy':
            targetValue = source

    return targetValue


# Set pandas options
set_option('display.max_colwidth', 0)

parser = ArgumentParser(description="Transform data in this csv file")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-objdir", help="The directory that contains text files for each object's fields that are to be extracted")
parser.add_argument("-datadir", help="The directory to containing the input csv files")
parser.add_argument("-stagedir", help="The directory to store the csv files of the transformed data")
parser.add_argument("-logfile", help="The path to the log file")
args = parser.parse_args()

#Get parameters from arguments
org =  args.org
objdir = args.objdir
datadir = args.datadir
stagedir = args.stagedir
logfile = args.logfile

# Get general configuration info
config = json.load(open('config_' + org + '.json')) 
sfsystemfields = config['transform_sf_system_fields'] 

files = getSortedFiles(datadir)
prev_sf_object_name = ''
csv_header = []
csv_row = []
csv_rows = []

# Get all data csv file in the input directory
for idx, datafile in enumerate(files):
    if datafile.endswith(".csv"):
        file_name = str(datafile)
        source_file_path = Path(datadir+'\\'+file_name)
        stage_file_path = Path(stagedir+'/'+str(source_file_path.parent.name)+'/'+file_name)

        sf_object_name = Path(file_name).stem

        #**************************************************
        # Load mapper into df
        #**************************************************
        if sf_object_name != prev_sf_object_name:
            prev_sf_object_name = sf_object_name
            fields_file_path = objdir + '/' + sf_object_name + '.txt'

            with open(fields_file_path, 'r', encoding='utf-8') as file:
                mapper = file.read().replace('\n', '')
                # When the configuration file is a JSON string the field names are in a mapping sheet located by the JSON attributes
                if (isValidJSON(mapper)):
                     sourcef, transf, targetf, mapper = getFieldNames(mapper, objdir, 'mapper')
                     writeToLog(logfile, 'Transformation data fields for ' + sf_object_name + ':\n' + mapper.to_markdown())

        writeToLog(logfile, 'Starting data transformation on file ' + str(source_file_path))

        # Read through source file and transform fields to target value and save to array
        try:
            with open(source_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                field_names = reader.fieldnames
                system_field_names = ['createddate','lastmodifieddate','createdbyid','lastmodifiedbyid']

                for idx, row in enumerate(reader):                
                    #**************************************************
                    #TODO: remove idx limit
                    #**************************************************
                    #if idx < 20:
                        csv_row = []

                        for field_name, field_value in row.items():
                            try:
                                # System fields are assumed to be copied to target
                                if (field_name.lower() in system_field_names):
                                    if sfsystemfields:
                                        if field_name not in csv_header:
                                            csv_header.append(field_name)
                                        csv_row.append(field_value)  
                                elif field_name.lower() == 'systemmodstamp': 
                                    pass
                                else:    
                                    # Find the transformation mapper row from df by locating the row with the same source column name. 
                                    mapper_row = mapper.loc[mapper[sourcef]==field_name]
                                    # Execute the transformation
                                    transValue = TransformData(field_value, str(mapper_row[transf].item()))

                                    try:
                                        if not(transValue == '*No Data*'):
                                            # Write cav header row
                                            if mapper_row[targetf].item() not in csv_header:
                                                csv_header.append(mapper_row[targetf].item())
                                            csv_row.append(transValue)  

                                                #writeToLog(logfile, 'cvs header ' + str(csv_header))
                                                #writeToLog(logfile, 'csv row ' + str(csv_row))

                                    except Exception as e:
                                        writeToLog(logfile, 'Error on transforming data row ' + field_name + ' ' + str(e))

                            except Exception as e:
                                writeToLog(logfile, 'Field mapping seek error for ' + field_name + ' ' + str(e))

                        csv_rows.append(csv_row)    

                        sys.stdout.write(f"{idx+1} records processed \r")
                        sys.stdout.flush()

                # Create stage aub directory if don't exist
                directory = os.path.dirname(stage_file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                    writeToLog(logfile, 'Created directory ' + str(directory))

                with open(stage_file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(csv_header)
                    writer.writerows(csv_rows)

        except FileNotFoundError:
            writeToLog(logfile, 'File ' + str(source_file_path) + ' not found.')
        except Exception as e:
            writeToLog(logfile, 'Error on transforming data in file ' + str(source_file_path) + ' ' + str(e))

        writeToLog(logfile, 'Completed data transformation on file ' + str(source_file_path) + ' for ' + str(len(csv_rows)) + ' records saved data to ' + str(stage_file_path))
