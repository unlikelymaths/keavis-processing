import logging

import config
from util import setup_logging
from dataloader.dataloader import run_loader
from dataloader.bin import BinIterator

from model.wenmf import WENMF

def run_models():
    logging.info('Running Models')
    with WENMF() as topicmodel:
        for bin in BinIterator():            
            logging.info('Adding Bin {}'.format(bin.start_time))
            topicmodel.add_bin(bin)
            
            # Check if the next bin will be a new frame
            current_bin_frame = config.get_frame(bin.start_time)
            next_bin_frame = config.get_frame(bin.start_time + config.binsize)
            if current_bin_frame != next_bin_frame:
                logging.info('Frame {} Finished'.format(current_bin_frame))
                topicmodel.finish_frame(current_bin_frame)

if __name__ == "__main__":
    setup_logging()
    logging.info('Staring Processing')
    
    run_loader()
    run_models()