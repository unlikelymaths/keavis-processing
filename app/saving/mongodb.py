import pymongo

class MongoDBSaver():

    def __init__(self):
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db = client.my_database

    def clear(self):
        self.db.topics.drop()
        self.db.topicframes.drop()
        self.db.topicbins.drop()
        self.db.framesummaries.drop()
        self.db.topicframes.create_index([('topic_id', pymongo.ASCENDING),
                                          ('frame', pymongo.ASCENDING)])
                                          
    def save_topic_bin(self,topic_bin):
        if '_id' in topic_bin.data:
            self.db.topicbins.replace_one({"_id": topic_bin.data['_id']}, topic_bin.data)
        else:
            topic_bin.data['_id'] = self.db.topicbin.insert_one(topic_bin.data).inserted_id
            
    def save_topic_frame(self,topic_frame):
        if '_id' in topic_frame.data:
            self.db.topicframes.replace_one({"_id": topic_frame.data['_id']}, topic_frame.data)
        else:
            topic_frame.data['_id'] = self.db.topicframe.insert_one(topic_frame.data).inserted_id
            
    def save_topic(self,topic):
        if '_id' in topic.data:
            self.db.topic.replace_one({"_id": topic.data['_id']}, topic.data)
        else:
            topic.data['_id'] = self.db.topic.insert_one(topic.data).inserted_id
            
    def save_framesummary(self,framesummary):
        self.db.framesummary.insert_one(framesummary)