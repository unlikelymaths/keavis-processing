import logging
import numpy as np
from sklearn.decomposition import NMF as NMFSklearn
from sklearn.preprocessing import normalize
from scipy.sparse.linalg import eigs, LinearOperator

from config import num_tokens
from util import load_json, save_json
from tools.tokenizer_w2v import W2VTokenizer
from tools.vocab import Vocab
from base.topic import TopicFrame

settings = {
    'initial_topics': 30,
    'sliding_window_size': 8,
    'min_tokens': 2,
    }

class WENMF():
    def __enter__(self):
        self.tokenizer = W2VTokenizer()
        self.vocab = Vocab()
        self.bins = load_json('./data/wenmf/bins.json', [])
        status = load_json('./data/wenmf/state.json',
            {
                'initial_done': False,
            })
        self.topic_frames = []
        self.initial_done = status['initial_done']
        return self

    def __exit__(self, type, value, tb):
        pass

    @property
    def num_topics(self):
        if self.W is not None:
            return self.W.shape[1]
        return 0

    def topicwords(self, topic):
        topicwords = []
        # Get corresponding column and sort descending
        w = self.W[:,topic].flatten()
        sorted_idcs = np.argsort(w)[::-1]
        # Take the first num_tokens
        for idx in sorted_idcs[:num_tokens]:
            token = self.vocab.cur_dict[idx]
            token = token.lower().replace('_',' ')
            topicwords.append((token, w[idx]))
        return topicwords

    def tokenize_bin(self, bin):
        tweets = []
        for tweet in bin:
            tokens = self.tokenizer.tokenize(tweet.text)
            if len(tokens) >= settings['min_tokens']:
                tweet.tokens = tokens
                tweets.append(tweet)
        bin.tweets = tweets

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
        max_iter = 200      # Maximum number of iterations
        eps = 1e-16         # Mimum value of H, small positive value for stability
        omega = 0.5         # For the extrapolation of the update
        threshold = 1e-16   # To stop updates
        reglambda = 20 * self.X.shape[1] / self.W_pre.shape[1]
        
        vtvlambda_norm = self.compute_norm(reglambda)
        Wp1 = self.W.copy()
        Wp2 = self.W.copy()
        Hp1 = self.H.copy()
        Hp2 = self.H.copy()
        
        for iteration in range(max_iter):
            W_hat = Wp1 + omega * (Wp1 - Wp2)
            H_hat = Hp1 + omega * (Hp1 - Hp2)
            
            for r in range(self.num_topics):
                idx = [i for i in range(self.num_topics) if i!=r]
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
            
            for r in range(self.num_topics):
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
                logging.debug('min_add_topic_strengh={}'.format(min_add_topic_strengh))
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
        logging.debug('Number of topics: {}'.format(self.num_topics))

    def summarize_bin(self):
        # Save results of the last bin
        last_bin = self.bins[-1]
        h = self.H[:,-len(last_bin):]

        # Normalize columns of h and get maximum
        h = normalize(h, axis=0)
        topic_assignment = np.argmax(h, axis=0)

        # Update topic_frames
        for topic in range(self.num_topics):
            # Add new topic frames if necessary
            if not topic < len(self.topic_frames):
                self.topic_frames.append(TopicFrame())
            # Push the current bin and the topicwords
            self.topic_frames[topic].push_bin(last_bin, self.topicwords(topic))

        # Push all tweets
        for idx, tweet in enumerate(last_bin):
            topic = topic_assignment[idx]
            tweet.weight = h[topic,idx]
            self.topic_frames[topic].push_tweet(tweet)

    def add_bin(self, bin):
        self.tokenize_bin(bin)    
        if self.initial_done:
            # Update the bins list
            old_bin = self.bins[0]
            self.bins = self.bins[1:] + [bin]

            # Update the vocabulary, the data matrix, and the embedding matrix
            self.vocab.update(bin, old_bin)
            keep_mask = np.invert(self.vocab.last_remove_mask)
            self.X = self.vocab.count_matrix(self.bins, normalized = True)
            self.update_v_mat()

            # Add rows for new words and remove rows of removed words
            self.W = np.vstack((self.W, 
                np.full((self.vocab.last_add_count,self.W.shape[1]),1e-16)))
            self.W = self.W[keep_mask,:]

            # Remove columns of the last bin and add columns for new bin
            self.H = self.H[:,len(old_bin):]
            self.H = np.hstack((self.H,
                0.001 * np.random.rand(self.H.shape[0], len(bin))))

            # Run the factorization and store the results
            self.update_model()
            self.summarize_bin()
        else:
            # Add data
            self.vocab.update(bin, []) 
            self.bins = self.bins + [bin]

    def finish_frame(self, frame):
        if self.initial_done:
            # Add all topic frames to the frame
            frame.push_topics(self.topic_frames)

            # Compute summed weights of all topics
            topic_strengths = np.mean(self.H / np.sum(self.H,0), 1)
            keep_mask = (topic_strengths >= (0.1 / settings['initial_topics']))
            
            # Remove entries from W, H, and topic_frames
            self.W = self.W[:,keep_mask]
            self.H = self.H[keep_mask,:]
            next_topic_frames = []
            for idx, topic_frame in enumerate(self.topic_frames):
                if keep_mask[idx]:
                    next_topic_frames.append(topic_frame.get_next())
            self.topic_frames = next_topic_frames
            logging.debug('Number of topics down to: {}'.format(self.num_topics))
        else:
            # Do not save the frame
            frame.discard()

            # Compute the solution to standard NMF for initialization
            logging.debug('Initial NMF')
            self.X = self.vocab.count_matrix(self.bins, normalized = True)
            model = NMFSklearn(settings['initial_topics'], init='nndsvd')
            self.W = model.fit_transform(self.X)
            self.H = model.components_

            # Run the wenmf
            self.initial_wenmf()

            # Remove bins
            while len(self.bins) > settings['sliding_window_size']:
                self.vocab.update([], self.bins[0])
                keep_mask = np.invert(self.vocab.last_remove_mask)
                self.W = self.W[keep_mask,:]
                self.H = self.H[:,len(self.bins[0]):]
                self.bins = self.bins[1:]
            self.initial_done = True
            self.X = None
