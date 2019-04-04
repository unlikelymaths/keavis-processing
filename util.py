import json
import logging
from os import path, makedirs
from datetime import datetime

timeformat = '%Y-%m-%d %H.%M.%S %z'
def time_to_str(time):
    if isinstance(time, str):
        return time
    return time.strftime(timeformat)
def str_to_time(time):
    if isinstance(time, str):
        return datetime.strptime(time,timeformat)
    return time

def setup_logging():
    no_logging = ['botocore', 'boto3', 'urllib3', 's3transfer']
    logging.basicConfig(level=logging.DEBUG,
                        filename='./data/processing.log', 
                        filemode='a', 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    for l in no_logging:
        logging.getLogger(l).setLevel(logging.WARNING)
    logging.getLogger().addHandler(logging.StreamHandler())

def ensure_dir(path_name):
    dirname = path.dirname(path_name)
    if not path.exists(dirname):
        makedirs(dirname)
        
def load_json(filename, default = {}):
    ensure_dir(filename)
    if path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    return default
        
def save_json(filename, data, indent=2):
    ensure_dir(filename)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=indent, ensure_ascii=False)
        
class JsonArrayWriter():
    def __init__(self,filename):
        self.filename = filename
        self.entries = 0

    def __enter__(self):
        self.file = open(self.filename, "w", encoding="utf-8")
        self.file.write("[\n\t")
        return self
        
    def __exit__(self, type, value, traceback):
        self.file.write("\n]")
        self.file.close()
    
    def write(self,data):
        if self.entries:
            self.file.write(",\n\t")
        self.entries += 1
        jsonstr = json.dumps(data)
        self.file.write(jsonstr)