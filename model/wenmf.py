import logging
import numpy as np
from sklearn.decomposition import NMF as NMFSklearn
from sklearn.preprocessing import normalize
from scipy.sparse.linalg import eigs, LinearOperator

from util import ensure_dir, load_json, save_json
from tools.tokenizer_default import DefaultTokenizer
from tools.tokenizer_w2v import W2VTokenizer
from tools.vocab import Vocab
from saving.topic import Topic, TopicFrame, TopicBin, make_framesummary

settings = {
    'initial_topics': 30,
    'sliding_window_size': 8,
    'num_tokens': 30,
    'min_tokens': 2,
    }



class WENMF():
    def __enter__(self):
        self.pre_first_run = True
        
        self.tokenizer = W2VTokenizer()
        self.vocab = Vocab()
        self.bins = load_json('./data/wenmf/bins.json', [])
        status = load_json('./data/wenmf/start_times.json',
            {
                'initial_done': False,
                'start_times': [],
            })
        self.initial_done = status['initial_done']
        self.start_times = status['start_times']
        return self

    def __exit__(self, type, value, tb):
        #save_json('./data/wenmf/bins.json', self.bins, indent=0)
        pass
        
    def tokenize_bin(self, raw_bin):
        bin = []
        for tweet in raw_bin.tweets:
            tokens = self.tokenizer.tokenize(tweet['text'])
            if len(tokens) >= settings['min_tokens']:
                tokenized_tweet = tweet.copy()
                del tokenized_tweet['text']
                tokenized_tweet['tokens'] = tokens
                bin.append(tokenized_tweet)
        return bin
    
    def w_to_topicwords(self, w, vocab):
        w = w.flatten()
        sorted_idcs = np.argsort(w)
        topicwords = []
        for idx in sorted_idcs[-settings['num_tokens']:][::-1]:
            token = vocab.cur_dict[idx]
            token = token.lower().replace('_',' ')
            topicwords.append((token, w[idx]))
        return topicwords
    
    def compute_norm(self, reglambda = 0):
        # Load the vocab
        vocab = self.vocab.cur_dict
        op = LinearOperator((len(vocab),len(vocab)), 
                            matvec = lambda x: reglambda * x + self.v_mat.transpose() @ (self.v_mat @ x))
        w,v = eigs(op,
                   k = 1,
                   which = 'LM',
                   maxiter = 100)
        return np.real(w[0])
        
    
    def update_v_mat(self):
        # Load the embeddings
        embedding_model = self.tokenizer.embedding_model
        embeddings = embedding_model.get_embeddings()
        vector_size = embedding_model.vector_size()
        
        # Load the vocab
        vocab = self.vocab.cur_dict
        
        # construct V
        v_shape = (vector_size, len(vocab))
        self.v_mat = np.zeros(v_shape)
        for idx, token in enumerate(vocab):
            self.v_mat[:,idx] = embeddings[token]
        
        # compute norm of VTV
        self.vtv_norm = self.compute_norm()
    
    
    def initial_wenmf(self):
        print('Initial WENMF')
        max_iter = 200      # Maximum number of iterations
        eps = 1e-16         # Mimum value of H, small positive value for stability
        omega = 0.5         # For the extrapolation of the update
        threshold = 1e-16   # To stop updates
        num_topics = self.W.shape[1]
        
        self.update_v_mat()
        Wp1 = self.W.copy()
        Wp2 = self.W.copy()
        Hp1 = self.H.copy()
        Hp2 = self.H.copy()
        
        for iteration in range(max_iter):
            W_hat = Wp1 + omega * (Wp1 - Wp2)
            H_hat = Hp1 + omega * (Hp1 - Hp2)
            
            for r in range(num_topics):
                idx = [i for i in range(num_topics) if i!=r]
                g = -2 * (self.v_mat.T @ (self.v_mat @ 
                            ((self.X @ self.H[None,r,:].T) - 
                             (self.W[:,idx] @ (self.H[idx,:] @ self.H[None,r,:].T) - 
                              W_hat[:,r,None] @ (self.H[None,r,:] @ self.H[None,r,:].T)))))
                L = 2 * np.abs(self.H[None,r,:] @ self.H[None,r,:].T) * self.vtv_norm
                self.W[:,r,None] = np.maximum(W_hat[:,r,None] - g / L, eps)
                sum_wr = np.sum(self.W[:,r])
                self.W[:,r] /= sum_wr
                self.H[r,:] *= sum_wr
            mean_w_change = np.max(np.abs((self.W - Wp1) / Wp1))
            
            for r in range(num_topics):
                tmp = ((self.v_mat @ self.W[:,r,None]).T @ self.v_mat)
                g = -2 * (tmp @ self.X - 
                          ((tmp @ self.W) @ self.H - (tmp @ self.W[:,r,None]) @ self.H[None,r,:]) -
                          (tmp @ self.W[:,r,None]) @ H_hat[None,r,:])
                L = 2 * np.sum(np.square(self.v_mat @ self.W[:,r,None]))
                self.H[None,r,:] = np.maximum(H_hat[None,r,:] - g / L, eps)
            mean_h_change = np.max(np.abs((self.H - Hp1) / Hp1))
            
            Wp2 = Wp1
            Hp2 = Hp1
            Wp1 = self.W
            Hp1 = self.H
                           
            if mean_w_change < threshold and mean_h_change < threshold:
                break
    
    def wenmf(self):
        #print('WENMF')
        max_iter = 200      # Maximum number of iterations
        eps = 1e-16         # Mimum value of H, small positive value for stability
        omega = 0.5         # For the extrapolation of the update
        threshold = 1e-16   # To stop updates
        num_topics = self.W.shape[1]
        reglambda = 20 * self.X.shape[1] / self.W_pre.shape[1]
        
        vtvlambda_norm = self.compute_norm(reglambda)
        Wp1 = self.W.copy()
        Wp2 = self.W.copy()
        Hp1 = self.H.copy()
        Hp2 = self.H.copy()
        
        for iteration in range(max_iter):
            W_hat = Wp1 + omega * (Wp1 - Wp2)
            H_hat = Hp1 + omega * (Hp1 - Hp2)
            
            for r in range(num_topics):
                idx = [i for i in range(num_topics) if i!=r]
                g = -2 * (self.v_mat.T @ (self.v_mat @ 
                            ((self.X @ self.H[None,r,:].T) - 
                             (self.W[:,idx] @ (self.H[idx,:] @ self.H[None,r,:].T) - 
                              W_hat[:,r,None] @ (self.H[None,r,:] @ self.H[None,r,:].T)))))
                L = 2 * np.abs(self.H[None,r,:] @ self.H[None,r,:].T)
                if r < self.W_pre.shape[1]:
                    g += 2 * reglambda * (W_hat[:,r,None] - self.W_pre[:,r,None])
                    L *= vtvlambda_norm
                else:
                    L *= self.vtv_norm
                self.W[:,r,None] = np.maximum(W_hat[:,r,None] - g / L, eps)
                sum_wr = np.sum(self.W[:,r])
                self.W[:,r] /= sum_wr
                self.H[r,:] *= sum_wr
            mean_w_change = np.max(np.abs((self.W - Wp1) / Wp1))
            
            for r in range(num_topics):
                tmp = ((self.v_mat @ self.W[:,r,None]).T @ self.v_mat)
                g = -2 * (tmp @ self.X - 
                          ((tmp @ self.W) @ self.H - (tmp @ self.W[:,r,None]) @ self.H[None,r,:]) -
                          (tmp @ self.W[:,r,None]) @ H_hat[None,r,:])
                L = 2 * np.sum(np.square(self.v_mat @ self.W[:,r,None]))
                self.H[None,r,:] = np.maximum(H_hat[None,r,:] - g / L, eps)
            mean_h_change = np.max(np.abs((self.H - Hp1) / Hp1))
            
            Wp2 = Wp1
            Hp2 = Hp1
            Wp1 = self.W
            Hp1 = self.H
                           
            if mean_w_change < threshold and mean_h_change < threshold:
                break
        print('Done after {} iterations'.format(iteration + 1))
        
        
    def update_model(self):
        logging.debug('update_model')
        self.W_pre = self.W.copy()
        
        for add_topics in range(5):
            logging.debug('Test {} additional topic(s)'.format(add_topics))
            if add_topics > 0:
                self.W = np.hstack((self.W, np.random.rand(self.W.shape[0],1)))
                self.W[:,-1] /= np.sum(self.W[:,-1])
                self.H = np.vstack((self.H, 0.001 * np.random.rand(1,self.H.shape[1])))
            self.wenmf()
            
            if add_topics > 0:
                min_add_topic_strengh = np.min(np.mean(self.H[-add_topics:,:] / np.sum(self.H,0), 1))
                #print('min_add_topic_strengh={}'.format(min_add_topic_strengh))
                if min_add_topic_strengh < 1 / settings['initial_topics']:
                    break
                else:
                    self.finalW = self.W
                    self.finalH = self.H
            else:
                self.finalW = self.W
                self.finalH = self.H
        self.W = self.finalW
        self.H = self.finalH
        print('Number of topics: {}'.format(self.W.shape[1]))
        
        
    def summarize_bin(self):
        topic_assignment = np.argmax(self.H[:,-len(self.bins[-1]):], axis=0)
        num_topics = self.W.shape[1]
        heatmaps = [[] for i in range(num_topics)]
        counts = [0] * num_topics
        for idx, tweet in enumerate(self.bins[-1]):
            if tweet['coordinates']:
                heatmaps[topic_assignment[idx]].append(tweet['coordinates'])
            counts[topic_assignment[idx]] += 1
        topicwords = [self.w_to_topicwords(self.W[:,i],self.vocab) 
                      for i in range(num_topics)]
        self.binresults.append({
            'num_topics': num_topics,
            'start_time': self.start_times[-1],
            'heatmaps': heatmaps,
            'counts': counts,
            'topicwords': topicwords,
            })
                    
                    
    def add_bin(self, bin):
        new_bin = self.tokenize_bin(bin)    
        if self.initial_done:
            old_bin = self.bins[0]
            self.bins = self.bins[1:] + [new_bin]
            self.start_times = self.start_times[1:] + [bin.start_time]
            self.vocab.update(new_bin, old_bin) 
            
            keep_mask = np.invert(self.vocab.last_remove_mask)
            
            self.W = np.vstack((self.W, 
                np.full((self.vocab.last_add_count,self.W.shape[1]),1e-16)))
            self.W = self.W[keep_mask,:]
                
            self.H = self.H[:,len(old_bin):]
            self.H = np.hstack((self.H,
                0.001 * np.random.rand(self.H.shape[0], len(new_bin))))
            self.X = self.vocab.count_matrix(self.bins, normalized = True)
            self.update_v_mat()
            
            self.update_model()
            self.summarize_bin()
        else:
            self.vocab.update(new_bin, []) 
            self.bins = self.bins + [new_bin]
            self.start_times = self.start_times + [bin.start_time]
            
    def finish_frame(self, frame):
        if self.initial_done:
            num_topics = self.W.shape[1]
            while len(self.topics) < num_topics:
                self.topics.append(Topic())
            topicframes = [TopicFrame(topic, frame) for topic in self.topics] 
            for bin in self.binresults:
                start_time = bin['start_time']
                for r in range(bin['num_topics']):
                    topicbin = TopicBin(topicframes[r], start_time)
                    topicbin.set_heatmap(bin['heatmaps'][r])
                    topicbin.set_count(bin['counts'][r])
                    topicbin.set_topicwords(bin['topicwords'][r])
                    topicbin.save()
                 
            for topicframe in topicframes:
                sorted_idcs = np.argsort([entry[1] for entry in topicframe.data['tokens']])
                topicwords = []
                for idx in sorted_idcs[-settings['num_tokens']:][::-1]:
                    topicwords.append(topicframe.data['tokens'][idx])
                topicframe.data['tokens'] = topicwords
                topicframe.save()
                
            for topic in self.topics:
                topic.save()
                
            make_framesummary(frame, topicframes)
            
            self.binresults = []
            topic_strengths = np.mean(self.H / np.sum(self.H,0), 1)
            keep_mask = (topic_strengths >= (0.1 / settings['initial_topics']))
            self.W = self.W[:,keep_mask]
            self.H = self.H[keep_mask,:]
            print('Number of topics down to: {}'.format(self.W.shape[1]))
            for topic_idx in range(num_topics,0,-1):
                if not keep_mask[topic_idx-1]:
                    del self.topics[topic_idx-1]
        else:
            print('Preparing initial WENMF')
            self.X = self.vocab.count_matrix(self.bins, normalized = True)
            model = NMFSklearn(settings['initial_topics'], init='nndsvd')
            self.W = model.fit_transform(self.X)
            self.H = model.components_
            self.initial_wenmf()
            while len(self.bins) > settings['sliding_window_size']:
                self.vocab.update([], self.bins[0])
                keep_mask = np.invert(self.vocab.last_remove_mask)
                self.W = self.W[keep_mask,:]
                self.H = self.H[:,len(self.bins[0]):]
                self.bins = self.bins[1:]
                self.start_times = self.start_times[1:]
            self.initial_done = True
            self.X = None
            self.binresults = []
            self.topics = []