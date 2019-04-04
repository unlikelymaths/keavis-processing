import logging
import zipfile
import json
from os import listdir, remove
from os.path import join

from config import first_bin, binsize
from util import load_json, save_json, time_to_str

from dataloader.bin import Bin, BinFilled
from dataloader.parser import parse_tweet
from dataloader.aws_download import aws_path

state_path = './data/binning_state.json'
last_bin = None

def load_state():
    return load_json(state_path, {'next_bin': time_to_str(first_bin)})
def save_state(state):
    return save_json(state_path, state)

def get_file_list():
    files = listdir(aws_path)
    return [(file, join(aws_path,file)) for file in files]
    
def load_tweet(line):
    tweet = json.loads(line)
    return parse_tweet(tweet)
       
def finish_bin(state, bin):
    print('Finishing Bin {}'.format(bin.start_time))
    bin.save()
    state['next_bin'] = time_to_str(bin.end_time)
    save_state(state)
       
def parse_file(jsonfile):
    state = load_state()
    if last_bin:
        current_bin = last_bin
    else:
        current_bin = Bin(state['next_bin'])
    for line in jsonfile:
        tweet = load_tweet(line)
        
        try:
            current_bin.append(tweet)
        except BinFilled:
            finish_bin(state, current_bin)
            current_bin = Bin(tweets = [tweet])
    finish_bin(state, current_bin)
    
    
def binning():
    logging.info('Binning Files')
    for fname, fpath in get_file_list():
        logging.info('Binning {}'.format(fname))
        with zipfile.ZipFile(fpath) as zip:
            filename = fname.split('.')[0] + '.txt'
            with zip.open(filename) as jsonfile:
                parse_file(jsonfile)
        remove(fpath)