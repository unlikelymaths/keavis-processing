"""This module provides bins to group tweets"""

from os import listdir, path
from math import floor

from config import binsize, bin_name, first_bin, paths
from util import ensure_dir, load_pickle, save_pickle

class BinFilled(Exception):
    """Raised when a tweet belonging to a subsequent bin is added"""

class Bin():
    """Groups tweets that were created within a certain time window."""

    def __init__(self, time=None, tweets=None):
        if time is None and tweets:
            time = tweets[0].time
        self.start_time = None
        self.tweets = tweets or []
        self.id = None
        if time:
            self.set_times(time)

    def __str__(self):
        return 'Bin(id={},start_time={})'.format(self.id, self.start_time)

    def save(self):
        """Pickle the bin to a file."""
        if self.tweets:
            filename = 'bin_{:09d}.pickle'.format(self.id)
            filepath = path.join(paths['bin_path'], filename)
            save_pickle(filepath, self)

    def delete(self):
        """Remove the file of this bin."""
        pass

    def set_times(self, time):
        """Set the start time, id and name from time."""
        timedelta = time - first_bin
        self.id = floor(timedelta / binsize)
        self.start_time = first_bin + self.id * binsize
        self.name = bin_name(self.start_time)

    @property
    def end_time(self):
        """The end of this bin."""
        return self.start_time + binsize

    def __iter__(self):
        return iter(self.tweets)

    def __len__(self):
        return len(self.tweets)

    def append(self, tweet):
        """Add the tweet if it falls between start and end time."""
        if tweet is None or tweet.time < self.start_time:
            return
        if tweet.time < self.end_time:
            self.tweets.append(tweet)
        else:
            raise BinFilled()

class BinIterator:
    """Iterates and loads all bins in the bin path."""

    def __init__(self):
        self.bin_iter = None
        self.last_bin = None

    def __iter__(self):
        ensure_dir(paths['bin_path'])
        self.bin_iter = iter(listdir(paths['bin_path']))
        self.last_bin = None
        return self

    def __next__(self):
        if self.last_bin:
            self.last_bin.delete()
        filename = next(self.bin_iter)
        filepath = path.join(paths['bin_path'], filename)
        self.last_bin = load_pickle(filepath, None)
        return self.last_bin
