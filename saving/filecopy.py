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
        for topic_frame in frame.topic_frames:
            self.save_topicframe(frame, topic_frame)
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
        data['heatmapWeights'] = self.get_frame_heatmap_weights(frame)

        file_path = join(self.target_dir,
                         'framesummary',
                         str(frame.id))
        save_json(file_path, data, indent=0)

    def get_frame_heatmap_weights(self, frame):
        weights = []
        for weight in frame.heatmap.weights:
            if weight == 0:
                weights.append(0)
            else:
                weights.append([weight,[]])
        for bin_id in frame.bin_ids:
            bin_weights = frame.bin_heatmap(bin_id).weights
            for i in range(len(bin_weights)):
                if weights[i] != 0:
                    weights[i][1].append(bin_weights[i])
        return weights

    def save_topicframe(self, frame, topic_frame):
        data = {}
        data['topicId'] = topic_frame.topic_id
        data['frameId'] = topic_frame.frame_id
        data['tokenList'] = topic_frame.token_list
        data['tokenWeights'] = topic_frame.token_weights
        data['heatmapWeights'] = self.get_topicframe_heatmap_weights(frame,
            topic_frame)
        data['counts'] = topic_frame.counts

        file_path = join(self.target_dir,
                         'topicframe',
                         str(topic_frame.frame_id), 
                         str(topic_frame.topic_id))
        save_json(file_path, data, indent=0)

    def get_topicframe_heatmap_weights(self, frame, topic_frame):
        weights = []
        for weight in topic_frame.heatmap.weights:
            if weight == 0:
                weights.append(0)
            else:
                weights.append([weight,[]])
        for bin_id in frame.bin_ids:
            bin_weights = topic_frame.bin_heatmap(bin_id).weights
            for i in range(len(bin_weights)):
                if weights[i] != 0:
                    weights[i][1].append(bin_weights[i])
        return weights

    def save_frameids(self, frame):
        self.frame_ids.append(frame.id)
        file_path = join(self.target_dir,
                         'frameids')
        save_json(file_path, self.frame_ids, indent=0)
        save_pickle(self.frame_ids_path, self.frame_ids)