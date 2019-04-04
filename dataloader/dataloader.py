import logging
from dataloader.aws_download import aws_download
from dataloader.binning import binning


def run_loader():
    logging.info('Loading new data')
    file_count = aws_download()
    binning()