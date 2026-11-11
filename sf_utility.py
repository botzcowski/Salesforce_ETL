from datetime import date, datetime, tzinfo, timedelta
from pathlib import Path
import pandas as pd
import os, json, csv, sys

def writeToLog(filepath, msg):
    f = open(filepath, 'a') 

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outmsg = now + ' ' + msg
    print(outmsg)        

    f.write(outmsg+'\r')
    f.close() 

def saveCDCDate(filepath, date):
    f = open(filepath, '+w') 
    f.write(date)
    f.close() 

def getMaxEndDate(cdcdate, range):
    cdcdt = datetime.strptime(cdcdate, '%Y-%m-%dT%H:%M:%SZ')
    enddate = cdcdt + timedelta(days=range)
    if enddate < datetime.utcnow(): 
        enddate = enddate.replace(tzinfo=simple_utc()).isoformat()
        enddate = enddate.split("+")[0]+'Z'
        return enddate
    else:    
        return ''

def utcNow():
    now = datetime.utcnow().replace(tzinfo=simple_utc()).isoformat()
    now = now.split(".")[0]+'Z'
    return now

def isValidJSON(string):
    try:
        json.loads(string)
        return True
    except json.JSONDecodeError:
        return False
        
def getFieldNames(jsonstring, path, location):
    try:
        fieldsConfig = json.loads(jsonstring)
    except  json.JSONDecodeError as e:
        #TODO remove
        print('JSON load Exception ' + str(e))

    column_name = ''

    # We only handle excel format for now.
    match fieldsConfig['format']:
        case 'Excel':
            excel_file = fieldsConfig['file']
            match location:
                case 'source' | 'target':
                    if location == 'source':
                        column_name = fieldsConfig['source_field_column_name']
                    if location == 'target':
                        column_name = fieldsConfig['target_field_column_name']
  
                    df = pd.read_excel(path+'/'+excel_file)
                    # Select the specified column and drop empty cells (NaN values)
                    column_data = df[column_name].dropna()
                    # Convert all values in the column to string type
                    # This ensures that numbers, booleans, etc., are properly converted before joining
                    delimiter = ','
                    delimited_string = delimiter.join(column_data.astype(str))
                    return delimited_string
                case 'mapper':
                    df = pd.read_excel(path+'/'+excel_file, usecols=[fieldsConfig['source_field_column_name'], fieldsConfig['transformation_column_name'], fieldsConfig['target_field_column_name']])
                    return fieldsConfig['source_field_column_name'], fieldsConfig['transformation_column_name'], fieldsConfig['target_field_column_name'], df
                

def getSortedFiles(path):
    if not os.path.isdir(path):
        return []

    files = []
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isfile(full_path):
            files.append(entry)
    
    files.sort()  # Sorts the list of file names alphabetically
    return files

def readCsvData(filepath, encoding):
    #keys = []
    #data = []
    
    with open(filepath, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        #keys = reader.fieldnames 
        data = [row for row in reader]
        #for row in reader:
        #    data.append(row)  # Each row is a dictionary        
    return data

def querySf(sf, SOQL, objname, logfile):
    qryResult =	sf.query(SOQL)
    writeToLog(logfile, 'Total '+objname+' records extracted: ' + str(qryResult['totalSize']))

    noOfBatch = 1
    data = []
    keys = []
    isDone = qryResult['done'] 

    if isDone:
        for rec in qryResult['records']: 
            # Remove 'attributes' from dictionary      
            rec.pop('attributes', None) 
            keys.append(rec['Id'])
            data.append(rec) 
        sys.stdout.write(f"Getting batch {noOfBatch} of records for " + objname + "\r")
        sys.stdout.flush()                    
        return keys, data

    while not isDone:
        try:   
            if not qryResult['done']:
                noOfBatch+=1
                for rec in qryResult['records']: 
                    rec.pop('attributes', None) 
                    keys.append(rec['Id'])
                    data.append(rec)
                sys.stdout.write(f"Getting batch {noOfBatch} of records for " + objname + "\r")
                sys.stdout.flush()                    
                #writeToLog(logfile, 'Getting next batch of records for ' + objname)
                qryResult = sf.query_more(qryResult['nextRecordsUrl'], True)
            else:  
                for rec in qryResult['records']: 
                    rec.pop('attributes', None) 
                    keys.append(rec['Id'])
                    data.append(rec)
                    isDone = True
                writeToLog(logfile, 'Done getting ' + str(noOfBatch) + ' batches of records for ' + objname)
        except NameError:     
            for rec in qryResult['records']: 
                rec.pop('attributes', None) 
                keys.append(rec['Id'])
                data.append(rec)
            qryResult =	sf.query_more(qryResult['nextRecordsUrl'], True)
    return keys, data


def getSfResults(sf, job_id, sf_object_name, directory):
    file_path = str(Path(directory+'\\'+sf_object_name))  + '_' + job_id
    file = file_path + '_success.csv'
    # Get success records and write to file path
    result = sf.bulk2.__getattr__(sf_object_name).get_successful_records(job_id, file=file)

    file = file_path + '_error.csv'
    # Get failed records and write to file path
    result = sf.bulk2.__getattr__(sf_object_name).get_failed_records(job_id, file=file)

class simple_utc(tzinfo):
    def tzname(self,**kwargs):
        return "UTC"
    def utcoffset(self, dt):
        return timedelta(0)    

class Mapper:
    def __init__(self, source, transform, target):
        self.source = source
        self.transform = transform
        self.target = target