from saving import saver

def make_framesummary(frame, topicframes):
    topic_ids = [topicframe.data['topic_id'] for topicframe in topicframes]
    
    heatmap = []
    for topicframe in topicframes:
        heatmap += topicframe.data['heatmap']
    
    counts = []
    for topicframe in topicframes:
        for i, count in enumerate(topicframe.data['counts']):
            if len(counts) <= i:
                counts.append(0)
            counts[i] += count
            
    hotness = [(topicframe.data['counts'], topicframe.data['topic_id']) for topicframe in  topicframes]
    hotness.sort(key = lambda d: d[0], reverse = True)
    hot = [e[1] for e in hotness]
    
    framesummary = {'frame_id': frame['id'],
                    'frame_name': frame['name'],
                    'topic_ids': topic_ids,
                    'hot': hot,
                    'heatmap': heatmap,
                    'counts': counts}
    saver.save_framesummary(framesummary)

class TopicBin():
    def __init__(self, topicframe, start_time):
        self.topicframe = topicframe
        self.data = {'topic_id': topicframe.data['topic_id'],
                     'start_time': start_time,
                     'tokens': [],
                     'heatmap': [],
                     'count': 0}
        self.idx = self.topicframe.add_bin(start_time)
        
    def save(self):
        saver.save_topic_bin(self)
        
    def set_heatmap(self, heatmap):
        self.data['heatmap'] = heatmap.copy()
        self.topicframe.add_heatmap(heatmap)
        
    def set_count(self, count):
        self.data['count'] = count
        self.topicframe.set_bincount(self.idx, count)
    
    def set_topicwords(self, tokens):
        self.data['tokens'] = tokens
        self.topicframe.add_topicwords(tokens)
    
class TopicFrame():
    def __init__(self, topic, frame):
        self.topic = topic
        self.data = {'topic_id': topic.id(),
                     'frame_id': frame['id'],
                     'tokens': [],
                     'heatmap': [],
                     'counts': [],
                     'total': 0,
                     'bins': []}
        self.topic.add_frame(frame)
        
    def save(self):
        saver.save_topic_frame(self)
        
    def add_bin(self, start_time):
        self.data['bins'].append(start_time)
        self.data['counts'].append(0)
        return len(self.data['bins']) - 1
        
    def add_heatmap(self, heatmap):
        self.data['heatmap'] += heatmap
        
    def set_bincount(self, bin_idx, count):
        self.data['counts'][bin_idx] = count
        self.data['total'] = sum(self.data['counts'])
        
    def add_topicwords(self, tokens):
        for token, weight in tokens:
            elements = [idx 
                        for idx, entry in enumerate(self.data['tokens'])
                        if entry[0] == token]
            if len(elements) > 0:
                idx = elements[0]
                self.data['tokens'][idx] = (
                    self.data['tokens'][idx][0],
                    self.data['tokens'][idx][1] + weight)
            else:
                self.data['tokens'].append((token,weight))
        
        
class Topic():
    def __init__(self):
        self.data = {'first_frame_id': None,
                     'first_frame_id': None}
    
    def id(self):
        if '_id' not in self.data:
            self.save()
        return self.data['_id']
        
    def save(self):
        saver.save_topic(self)
    
    def add_frame(self, frame):
        if self.data['first_frame_id'] is None:
            self.data['first_frame_id'] = frame['id']
        self.data['last_frame_id'] = frame['id']
        
        
      