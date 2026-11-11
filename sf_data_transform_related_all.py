from sf_utility import writeToLog
from datetime import date
from argparse import ArgumentParser
from pathlib import Path
import subprocess

parser = ArgumentParser(description="Transform data in csv files")
parser.add_argument("-org", help="The client/organization's name")
parser.add_argument("-obj", help="The master object name")
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
# Get all staged data files to execute tranformation.
stagedir_path = Path(stagedir)
subdirs = [item for item in stagedir_path.rglob("*") if item.is_dir()]

for idx, subdir in enumerate(subdirs):
    writeToLog(logfile, 'Process files in ' + str(subdir) + ' for transformation')

    # Compose python execution string 
    execution_string = 'python3 sf_data_transform_related.py -org ' + org + ' -obj ' + master_object + ' -datadir ' + str(datadir) + ' -stagedir ' + str(subdir) + ' -logfile ' + str(logfile)

    processes.append(subprocess.Popen(["start", "/wait", "cmd.exe", "/K", execution_string], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True))

