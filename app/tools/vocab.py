import collections
from scipy import sparse
import numpy as np

class Vocab(object):
    def __init__(self, threshold = 2, grace_period = 0):
        """Construct a Vocab.

        attributes:
            threshold -- minimum count of the word for appearance in the
                         dictionary; i.e. the threshold of appearance.
            grace_period -- duration in epochs the word stays in the dict
                        even if its tokencount falls below the threshold
                        
        """
        self.threshold = threshold
        self.grace_period = grace_period
        self.tokencount = {}
        self.cur_dict = []
        self.cur_idx_dict = {}
        self.remove_candidate = {}
        self.last_add_count = 0
        self.last_remove_mask = None
    
    def update(self, add_bin, remove_bin):
        self.last_add_count = 0
        self.last_remove_mask = [False] * len(self.cur_dict)
        self._increase_count(add_bin)
        self._decrease_count(remove_bin)
        
        for token, count in self.tokencount.items():
            if count >= self.threshold:
                self._add_token(token)
            else:
                self._remove_word(token)
                
        self._delete_words()
    
    def has(self, token):
        return token in self.cur_idx_dict
        
    def count_matrix(self, bins, normalized = False):
        num_tweets = 0
        data, i, j = [], [], []
        for bin in bins:
            for tweet in bin:
                token_count = collections.Counter(tweet.tokens).most_common()
                count_sum = 0
                for token, count in token_count:
                    count_sum += count
                for token, count in token_count:
                    if self.has(token):
                        data.append(count / count_sum)
                        i.append(self.cur_idx_dict[token])
                        j.append(num_tweets)
                num_tweets += 1
        mat_shape = (len(self.cur_dict), num_tweets)
        return sparse.coo_matrix((data, (i, j)), shape=mat_shape).tocsc()

    def tfidf_matrix(self, bins):
        count_matrix = self.count_matrix(bins, normalized = False)
        # IDF
        word_occurence = np.squeeze(np.asarray((count_matrix > 0).astype(int).sum(axis=1))) + 1
        total_documents = count_matrix.shape[1]
        #idf = sparse.diags(np.log(total_documents / word_occurence), format='csc')
        idf = sparse.diags(np.log(total_documents / word_occurence), format='csc')
        # Normalize
        tfidf_mat = idf * count_matrix
        col_sum = np.maximum(np.squeeze(np.asarray(count_matrix.sum(axis=0))), 1)
        return tfidf_mat * sparse.diags(1 / col_sum, format='csc')
        
    def _count_tokens(self, bin):
        counter = collections.Counter()
        for tweet in bin:
            counter.update(collections.Counter(tweet.tokens))
        return counter.most_common()
    
    def _increase_count(self, add_bin):
        add_tokens = self._count_tokens(add_bin)
        for token, count in add_tokens:
            try:
                self.tokencount[token] += count
            except KeyError:
                self.tokencount[token] = count
                
    def _decrease_count(self, remove_bin):
        remove_tokens = self._count_tokens(remove_bin)
        for token, count in remove_tokens:
            if count > self.tokencount[token]:
                raise ValueError('cannot remove more than the current count.')
            self.tokencount[token] -= count
                  
    def _add_token(self, token):
        if self.has(token):
            if token in self.remove_candidate:
                del self.remove_candidate[token]
        else:
            self.cur_dict.append(token)
            self.cur_idx_dict[token] = len(self.cur_dict) - 1
            self.last_add_count += 1
    
    def _remove_word(self, token):
        if self.has(token):
            if not token in self.remove_candidate:
                self.remove_candidate[token] = 0
            if self.remove_candidate[token] < self.grace_period:
                self.remove_candidate[token] += 1
            else:
                self._mark_for_deletion(token)
    
    def _mark_for_deletion(self, token):
        self.last_remove_mask[self.cur_idx_dict[token]] = True
        
    def _delete_words(self):
        self.last_remove_mask += [False] * self.last_add_count
        new_dict = []
        for i, token in enumerate(self.cur_dict):
            if self.last_remove_mask[i]:
                del self.cur_idx_dict[token]
                del self.remove_candidate[token]
                if self.tokencount[token] == 0:
                    del self.tokencount[token]
            else: 
                new_dict.append(token)
                self.cur_idx_dict[token] = len(new_dict) - 1
        self.cur_dict = new_dict
