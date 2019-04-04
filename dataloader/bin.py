import logging
from datetime import datetime
from os import listdir

from config import binpath, binsize
from util import ensure_dir, JsonArrayWriter, load_json, time_to_str, str_to_time

class BinFilled(Exception):
    pass

class Bin():

    def __init__(self, start_time = None, tweets = []):
        if start_time is None:
            start_time = Bin.get_start_time(tweets[0]['created_at'])
        self.start_time = str_to_time(start_time)
        self.tweets = tweets
        self.end_time = self.start_time + binsize
            
    def get_start_time(tweet_time):
        tweet_time = str_to_time(tweet_time)
        start_time = datetime(year=tweet_time.year, 
                        month=tweet_time.month, 
                        day=tweet_time.day, 
                        tzinfo=tweet_time.tzinfo)
        while start_time + binsize <= tweet_time:
            start_time += binsize
        return start_time
        
    def append(self, tweet):
        if tweet is None:
            return
            
        tweet_time = str_to_time(tweet['created_at'])
        
        if tweet_time < self.start_time:
            return
            
        if tweet_time < self.end_time:
            self.tweets.append(tweet)
        else:
            raise BinFilled()
    
    def from_file(binname):
        filepath = binpath + binname
        tweets = load_json(filepath) 
        return Bin(binname, tweets)
            
    def save(self):
        ensure_dir(binpath)
        if len(self.tweets) == 0:
            return
        filepath = binpath + time_to_str(self.start_time)
        with JsonArrayWriter(filepath) as file:
            for tweet in self.tweets:
                file.write(tweet)
    
    def delete(self):
        pass
        
class BinIterator:
  def __iter__(self):
    ensure_dir(binpath)
    self.bins = listdir(binpath)
    self.idx = 0
    self.last_bin = None
    return self
    
  def __next__(self):
    if self.last_bin:
        self.last_bin.delete()
        
    if self.idx < len(self.bins):
        self.last_bin = Bin.from_file(self.bins[self.idx])
        self.idx += 1
        return self.last_bin
    else:
        raise StopIteration