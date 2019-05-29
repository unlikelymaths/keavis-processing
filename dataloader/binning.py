import logging
import zipfile
import json
from os import listdir, remove
from os.path import join

from config import first_bin, paths
from util import load_pickle, save_pickle
from base.tweet import Tweet
from base.bin import Bin, BinFilled

state_path = './data/binning_state.pickle'
last_bin = None

def load_state():
    return load_pickle(state_path, {'next_bin': first_bin})

def save_state(state):
    return save_pickle(state_path, state)

def get_file_list():
    files = listdir(paths['aws_path'])
    return [(file, join(paths['aws_path'],file)) for file in files]

def finish_bin(state, bin):
    logging.info('Finishing {}'.format(bin))
    bin.save()
    state['next_bin'] = bin.end_time
    save_state(state)

def parse_file(jsonfile):
    state = load_state()
    if last_bin:
        current_bin = last_bin
    else:
        current_bin = Bin(time = state['next_bin'])
    for line in jsonfile:
        tweet_data = json.loads(line)
        tweet = Tweet.from_tweet_data(tweet_data)
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
        #remove(fpath)