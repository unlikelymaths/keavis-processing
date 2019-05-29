from os.path import join
from config import bin_name_from_id
from util import save_json, time_to_str, load_pickle, save_pickle

class FileCopySaver():

    def __init__(self):
        self.target_dir = './upload/'
        self.frame_ids_path = './data/state/frameids.pickle'
        self.frame_ids = load_pickle(self.frame_ids_path, [])

    def save(self, frame):
        self.save_framesummary(frame)
        bin_ids = frame.bin_ids
        for topic_frame in frame.topic_frames:
            self.save_topicframe(topic_frame, bin_ids)
        self.save_frameids(frame)
        
    def save_framesummary(self, frame):
        data = {}
        data['id'] = frame.id
        data['name'] = frame.name
        data['topic_ids'] = frame.topic_ids
        data['bins'] = [(id, bin_name_from_id(id))
                        for id in frame.bin_ids]
        data['counts'] = frame.counts
        data['heatmapGrid'] = frame.heatmap.grid
        data['heatmapWeights'] = frame.heatmap.weights

        file_path = join(self.target_dir,
                         'framesummary',
                         str(frame.id))
        save_json(file_path, data, indent=0)

    def save_topicframe(self, topic_frame, bin_ids):
        data = {}
        data['topicId'] = topic_frame.topic_id
        data['frameId'] = topic_frame.frame_id
        data['tokenList'] = topic_frame.token_list
        data['tokenWeights'] = topic_frame.token_weights
        data['heatmapWeights'] = topic_frame.heatmap.weights
        data['counts'] = topic_frame.counts

        file_path = join(self.target_dir,
                         'topicframe',
                         str(topic_frame.frame_id), 
                         str(topic_frame.topic_id))
        save_json(file_path, data, indent=0)

    def save_frameids(self, frame):
        self.frame_ids.append(frame.id)
        file_path = join(self.target_dir,
                         'frameids')
        save_json(file_path, self.frame_ids, indent=0)
        save_pickle(self.frame_ids_path, self.frame_ids)