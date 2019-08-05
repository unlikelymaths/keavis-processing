import logging
import boto3
from time import sleep
from os.path import join

from util import ensure_dir, load_json, save_json
from config import default_timeout, download_retries, last_file, paths

from dataloader.server_settings import BUCKET_NAME

# State
state_path = './data/awsloader_state.json'
def load_state():
    return load_json(state_path, {'processed_files': [], 'last_file': last_file})
def save_state(state):
    return save_json(state_path, state)

    
# AWS Interface
def get_aws_filelist():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    return [object.key for object in bucket.objects.all()] 
def get_aws_file(filename, filepath):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    bucket.download_file(filename, filepath)
    
    
# Download Function
def download_new_files():
    file_count = 0
    aws_filelist = get_aws_filelist()
    state = load_state()
    new_files = [(file, join(paths['aws_path'],file)) for file in aws_filelist if file > state['last_file']]
    
    for filename, filepath in new_files:
        logging.debug('Downloading {} from AWS bucket.'.format(filename))
        get_aws_file(filename, filepath)
        state['processed_files'].append(filename)
        state['last_file'] = filename
        save_state(state)
        file_count += 1
        
    return file_count
    
    
def aws_download():
    logging.info('Downloading AWS Files')
    ensure_dir(paths['aws_path'])
    file_count = download_new_files()
    if file_count == 0:
        timeout = default_timeout
        for i in range(download_retries):
            logging.info('No new files found. Checking again in {} minutes.'.format(timeout/60))
            sleep(timeout)
            timeout = timeout * 2
            file_count = download_new_files()
    if file_count == 0:
        logging.warning('No new files downloaded. Aborting process.')
        exit()