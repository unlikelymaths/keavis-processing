from base.heatmap import Heatmap

class TopicBin():
    def __init__(self, bin, topicwords):
        self.id = bin.id
        self.topicwords = topicwords
        self.heatmap = Heatmap()
        self.tweets = []
        self.normalize_topicwords()

    def normalize_topicwords(self):
        total_weight = sum(topicword[1] for topicword in self.topicwords)
        for idx in range(len(self.topicwords)):
            self.topicwords[idx] = (self.topicwords[idx][0], 
                                    self.topicwords[idx][1] / total_weight)

    def push_tweet(self, tweet):
        self.tweets.append(tweet)
        if tweet.coords:
            self.heatmap.add(tweet.coords)

    @property
    def count(self):
        return len(self.tweets)

class TopicFrame():
    def __init__(self, topic_id = None):
        self.topic_id = topic_id
        self.frame_id = None
        self.bin_ids = None
        self.topic_bins = []
        self.ids = {}
        self.meta = {}
        self._heatmap = None

    def push_bin(self, bin, topicwords):
        self.topic_bins.append(TopicBin(bin, topicwords))
        self.ids[self.topic_bins[-1].id] = len(self.topic_bins) - 1

    def push_tweet(self, tweet):
        self.topic_bins[-1].push_tweet(tweet)

    def get_next(self):
        return TopicFrame(topic_id = self.topic_id)

    def bin_count(self,bin_id):
        try:
            return self.topic_bins[self.ids[bin_id]].count
        except KeyError:
            return 0

    @property
    def heatmap(self):
        if not self._heatmap:
            self._heatmap = Heatmap()
            for topic_bin in self.topic_bins:
                self._heatmap.add(topic_bin.heatmap)
        return self._heatmap

    def bin_heatmap(self, bin_id):
        try:
            return self.topic_bins[self.ids[bin_id]].heatmap
        except KeyError:
            return Heatmap()

    @property
    def token_list(self):
        tokens = set()
        for topic_bin in self.topic_bins:
            for topicword in topic_bin.topicwords:
                tokens = tokens | {topicword[0]}
        return list(tokens)

    @property
    def token_weights(self):
        token_list = self.token_list
        token_weights = [0,] * len(token_list)
        for topic_bin in self.topic_bins:
            for topicword in topic_bin.topicwords:
                idx = token_list.index(topicword[0])
                token_weights[idx] += topicword[1]
        num_bins = len(self.topic_bins)
        token_weights = [w / num_bins for w in token_weights]
        return token_weights

    def bin_token_weights(self, bin_id):
        token_list = self.token_list
        token_weights = [0,] * len(token_list)
        if bin_id not in self.ids:
            return token_weights
        for topicword in self.topic_bins[self.ids[bin_id]].topicwords:
            idx = token_list.index(topicword[0])
            token_weights[idx] += topicword[1]
        return token_weights

    @property
    def counts(self):
        counts = []
        for bin_id in self.bin_ids:
            try:
                bin_count = self.topic_bins[self.ids[bin_id]].count
            except KeyError:
                bin_count = 0
            counts.append(bin_count)
        return counts
