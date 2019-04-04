import re
import pytz
from datetime import datetime
from util import time_to_str

tweet_time_format = '%a %b %d %H:%M:%S %z %Y'
def parse_tweet_time(tweet, raw_tweet):
    time = datetime.strptime(raw_tweet['created_at'],'%a %b %d %H:%M:%S %z %Y').astimezone(pytz.utc)
    tweet['created_at'] = time_to_str(time)

    
    
def parse_text(tweet, raw_tweet):
    if(raw_tweet['truncated']):
        tweet['text'] = raw_tweet['extended_tweet']['full_text']
    else:
        tweet['text'] = raw_tweet['text']
      
      
      
bbox_min = (-119, 33)
bbox_max = (-117, 35)
def parse_coordinate(tweet, raw_tweet):
    coordinates = None
    if 'coordinates' in raw_tweet and raw_tweet['coordinates'] is not None:
        coordinates = raw_tweet['coordinates']['coordinates']
    elif 'place' in raw_tweet and raw_tweet['place']['place_type'] == 'poi':
        coordinates = raw_tweet["place"]["bounding_box"]["coordinates"][0][0]
    
    if coordinates is not None:
        coordinates = (float(coordinates[0]),float(coordinates[1]))
        if not(coordinates[0] >= bbox_min[0] and coordinates[0] <= bbox_max[0] and 
               coordinates[1] >= bbox_min[1] and coordinates[1] <= bbox_max[1]):
            coordinates = None
    
    tweet['coordinates'] = coordinates
    
    
    
source_re= re.compile('(?<=>)(.*)(?=<)')
def parse_source(tweet, raw_tweet):
    sourcename = raw_tweet['source']
    if(sourcename !=''):
        sourcename = source_re.search(sourcename).group(0)
    tweet['source'] = sourcename
    
    
    
def parse_user(tweet, raw_tweet):
    tweet['user_id'] = raw_tweet['user']['id']
    tweet['user_name'] = raw_tweet['user']['screen_name']
    tweet['user_posts'] = raw_tweet['user']['statuses_count']
    tweet['user_followers'] = raw_tweet['user']['followers_count']
    
    
    
def parse_place(tweet, raw_tweet):
    if 'place' in raw_tweet and raw_tweet['place'] is not None:
        tweet['place_id'] = raw_tweet['place']['id']
        tweet['place_name'] = raw_tweet['place']['name']
    else:
        tweet['place_id'] = None
        tweet['place_name'] = None
    
    
# May Return None to discard tweets
def parse_tweet(raw_tweet):
    tweet = {}
    
    tweet['id'] = raw_tweet['id']
    tweet['lang'] = raw_tweet['lang']
    tweet['in_reply_to_status_id'] = raw_tweet['in_reply_to_status_id']
    tweet['in_reply_to_user_id'] = raw_tweet['in_reply_to_user_id']
    
    parse_tweet_time(tweet, raw_tweet)
    parse_text(tweet, raw_tweet)
    parse_coordinate(tweet, raw_tweet)
    parse_source(tweet, raw_tweet)
    parse_user(tweet, raw_tweet)
    parse_place(tweet, raw_tweet)
    
    return tweet