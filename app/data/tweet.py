from typing import Dict
import re
import pytz
from datetime import datetime
from collections import namedtuple
from config import bbox_min, bbox_max

UserBase = namedtuple('UserBase', ('id','name','posts','followers'))
class User(UserBase):
    def from_tweet_data(tweet_data):
        user_data = {
            'id': tweet_data['user']['id'],
            'name': tweet_data['user']['screen_name'],
            'posts': tweet_data['user']['statuses_count'],
            'followers': tweet_data['user']['followers_count']}
        return User(**user_data)

PlaceBase = namedtuple('PlaceBase', ('id','name'))
class Place(PlaceBase):
    def from_tweet_data(tweet_data):
        if 'place' in tweet_data and tweet_data['place'] is not None:
            return Place(tweet_data['place']['id'],tweet_data['place']['name'])
        return None

class Tweet():
    time_format = '%a %b %d %H:%M:%S %z %Y'
    source_re = re.compile('(?<=>)(.*)(?=<)')

    def __init__(self):
        self.id = None
        self.lang = None
        self.in_reply_to_status_id = None
        self.in_reply_to_user_id = None
        self.text = None
        self.time = None
        self.coords = None
        self.source = None
        self.place = None
        self.user = None
        self.tokens = None
        self.weight = None

    def from_tweet_data(tweet_data: Dict):
        tweet = Tweet()
        tweet.id = tweet_data['id']
        tweet.lang = tweet_data['lang']
        tweet.in_reply_to_status_id = tweet_data['in_reply_to_status_id']
        tweet.in_reply_to_user_id = tweet_data['in_reply_to_user_id']
        tweet.text = Tweet.parse_text(tweet_data)
        tweet.time = Tweet.parse_time(tweet_data)
        tweet.coords = Tweet.parse_coords(tweet_data)
        tweet.source = Tweet.parse_source(tweet_data)
        tweet.place = Place.from_tweet_data(tweet_data)
        tweet.user = User.from_tweet_data(tweet_data)
        return tweet

    def parse_time(tweet_data: Dict):
        return datetime.strptime(
            tweet_data['created_at'],
            '%a %b %d %H:%M:%S %z %Y').astimezone(pytz.utc)

    def parse_text(tweet_data: Dict):
        if(tweet_data['truncated']):
            return tweet_data['extended_tweet']['full_text']
        else:
            return tweet_data['text']

    def parse_coords(tweet_data: Dict):
        coords = None
        if tweet_data.get('coordinates',None) is not None:
            coords = tweet_data['coordinates']['coordinates']
        elif 'place' in tweet_data and tweet_data['place']['place_type'] == 'poi':
            coords = tweet_data['place']['bounding_box']['coordinates'][0][0]
        if coords is not None:
            coords = (float(coords[0]),float(coords[1]))
            if not(coords[0] >= bbox_min[0] and coords[0] <= bbox_max[0] and 
                coords[1] >= bbox_min[1] and coords[1] <= bbox_max[1]):
                coords = None
        return coords

    def parse_source(tweet_data: Dict):
        source = tweet_data['source']
        if(source !=''):
            source = Tweet.source_re.search(source).group(0)
        return source