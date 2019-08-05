import boto3
import config

session = boto3.Session()
s3_resouce = session.resource('s3')

raw_bucket = s3_resouce.Bucket(config.raw_bucket_name)
intermediate_bucket = s3_resouce.Bucket(config.intermediate_bucket_name)
result_bucket = s3_resouce.Bucket(config.result_bucket_name)