"""Provides the Frame class to strore results"""

from util import load_pickle, save_pickle
from base.heatmap import Heatmap

class Frame():
    """A Frame stores all topics frames within a time window"""
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.discarded = False
        self.topic_frames = []
        self._heatmap = None
        self._bin_ids = None
        self.meta = {}

    def push_topics(self, topic_frames):
        self._heatmap = None
        self._bin_ids = None
        topicid_path = './data/state/topicid.pickle'
        topicid = load_pickle(topicid_path, 0)
        self.topic_frames = topic_frames
        for topic_frame in self.topic_frames:
            topic_frame.frame_id = self.id
            topic_frame.bin_ids = self.bin_ids
            if topic_frame.topic_id is None:
                topic_frame.topic_id = topicid
                topicid += 1
        topicid = save_pickle(topicid_path, topicid)

    def discard(self):
        self.discarded = True
        
    @property
    def bin_ids(self):
        if not self._bin_ids:
            bin_set = set()
            for topic_frame in self.topic_frames:
                for topic_bin in topic_frame.topic_bins:
                    bin_set = bin_set | {topic_bin.id}
            self._bin_ids = sorted(bin_set)
        return self._bin_ids

    @property
    def counts(self):
        counts = []
        for bin_id in self.bin_ids:
            count = 0
            for topic_frame in self.topic_frames:
                count += topic_frame.bin_count(bin_id)
            counts.append(count)
        return counts

    @property
    def topic_ids(self):
        return [topic_frame.topic_id for topic_frame in self.topic_frames]

    @property
    def heatmap(self):
        if not self._heatmap:
            print('build complete heatmap')
            self._heatmap = Heatmap()
            for topic_frame in self.topic_frames:
                self._heatmap.add(topic_frame.heatmap)
            print('reduce heatmap')
            self._heatmap.reduce()
        return self._heatmap

#    def save():
#        topic_ids = [topicframe.data['topic_id'] for topicframe in topicframes]
#
#        heatmap = []
#        for topicframe in topicframes:
#            heatmap += topicframe.data['heatmap']
#
#        counts = []
#        for topicframe in topicframes:
#            for i, count in enumerate(topicframe.data['counts']):
#                if len(counts) <= i:
#                    counts.append(0)
#                counts[i] += count
#
#        hotness = [(topicframe.data['counts'], topicframe.data['topic_id'])
#                   for topicframe in  topicframes]
#        hotness.sort(key=lambda d: d[0], reverse=True)
#        hot = [e[1] for e in hotness]
#
#        framesummary = {'frame_id': frame['id'],
#                        'frame_name': frame['name'],
#                        'topic_ids': topic_ids,
#                        'hot': hot,
#                        'heatmap': heatmap,
#                        'counts': counts}
#        saver.save_framesummary(framesummary)
