from os.path import join
from util import save_json, time_to_str

class FileCopySaver():

    def __init__(self):
        self.target_dir = './upload/'
        self.state = {'topic_id': 0}

    def clear(self):
        pass
     
    def new_topic_id(self):
        topic_id = self.state['topic_id']
        self.state['topic_id'] = topic_id + 1
        return topic_id 
        
    def save_topic_bin(self, topic_bin):
        data = topic_bin.data
        data['start_time'] = time_to_str(data['start_time'])
        folder_path = join(self.target_dir, 
                           'topicbin/{}'.format(data['topic_id']))
        filename = data['start_time']
        save_json(join(folder_path, filename), data, indent=0)
        
    def save_topic_frame(self, topic_frame):
        data = topic_frame.data
        data['bins'] = [time_to_str(bin) for bin in data['bins']]
        folder_path = join(self.target_dir, 
                           'topicframe/{}'.format(topic_frame.data['topic_id']))
        filename = str(topic_frame.data['frame_id'])
        save_json(join(folder_path, filename), topic_frame.data, indent=0)
            
    def save_topic(self, topic):
        if '_id' not in topic.data:
            topic.data['_id'] = self.new_topic_id()
        folder_path = join(self.target_dir,'topic')
        filename = str(topic.data['_id'])
        save_json(join(folder_path, filename), topic.data, indent=0)
        
    def save_framesummary(self, framesummary):
        folder_path = join(self.target_dir,'framesummary')
        filename = str(framesummary['frame_id'])
        save_json(join(folder_path, filename), framesummary, indent=0)