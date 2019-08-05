import logging
import config
from util import setup_logging
from dataloader.aws_download import aws_download
from dataloader.binning import binning
from base.bin import BinIterator
from base.frame import Frame

from model.wenmf import WENMF as Model
from saving.filecopy import FileCopySaver as Saver

def run_loader():
    logging.info('Loading new data')
    #aws_download()
    binning()

def run_models():
    logging.info('Running Models')
    saver = Saver()
    with Model() as topicmodel:
        for bin in BinIterator():
            logging.info('Adding {}'.format(bin))
            topicmodel.add_bin(bin)

            # Check if the next bin will be a new frame
            frame_id = config.frame_id(bin.start_time)
            next_frame_id = config.frame_id(bin.start_time + config.binsize)
            if frame_id != next_frame_id:
                frame_name = config.frame_name(bin.start_time)
                frame = Frame(frame_id, frame_name)
                logging.info('Frame {} Finished'.format(frame))
                topicmodel.finish_frame(frame)
                if frame.discarded == False:
                    saver.save(frame)

if __name__ == "__main__":
    setup_logging()
    logging.info('Starting Processing')

    #run_loader()
    run_models()
