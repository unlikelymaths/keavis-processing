import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
from gensim.models import KeyedVectors
import json
from operator import itemgetter
from difflib import get_close_matches
from os.path import isfile

exists_token = "###WORD_EXISTS###"

def _load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)
        
def _save_json(data,filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

class Word2vecModel():
    def __init__(self):
        self.vocab_loaded = False
        self.filter_loaded = False
        self.model_data = None
        self.embedding_filename = './data/embedding/word2vec.bin'
        self.vocab_filename = './data/embedding/word2vec.vocab.txt'
       
    def load_model(self):
        if self.model_data is None:
            print('Loading Model')
            self.model_data = KeyedVectors.load_word2vec_format(
                self.embedding_filename, binary=True)
            
    def vocab(self):
        if not self.vocab_loaded:
            if isfile(self.vocab_filename):
                self._vocab = _load_json(self.vocab_filename)
            else:
                self.load_model()
                self._vocab = [str(token) for token in self.model_data.vocab]
                _save_json(self._vocab, self.vocab_filename)
            self.vocab_loaded = True
        return self._vocab
    
    def vector_size(self):
        self.load_model()
        return self.model_data.wv.vector_size
        
    def get_embeddings(self):
        self.load_model()
        return self.model_data.wv
        
    def load_filter(self):
        if self.filter_loaded:
            return
        print('Creating Filter')
        self.filter_loaded = True
        self.lookup = {}
        vocab = self.vocab()
        for token in vocab:
            if '__' in token or token.startswith('_') or token.endswith('_'):
                continue
            words = token.replace("_"," ").split()
            if len(words) == 0:
                continue
            current_lookup = self.lookup
            for word in words:
                lower_word = word.lower()
                if not lower_word in current_lookup:
                    current_lookup[lower_word] = {}
                current_lookup = current_lookup[lower_word]
            if exists_token in current_lookup:
                #current_lookup[exists_token].append(token)
                pass
            else:
                current_lookup[exists_token] = [token,]
                
    def filter(self, all_tokens):
        self.load_filter()
        idx = 0
        tokens = []
        while idx < len(all_tokens):
            phrase = []
            valid = 0
            currentidx = idx
            current_lookup = self.lookup
            phrase_list = None
            while currentidx < len(all_tokens) and all_tokens[currentidx].lower() in current_lookup:
                phrase.append(all_tokens[currentidx])
                current_lookup = current_lookup[all_tokens[currentidx].lower()]
                if exists_token in current_lookup:
                    valid = len(phrase)
                    phrase_list = current_lookup[exists_token]
                currentidx = currentidx + 1
            
            if valid > 0:
                phrase = "_".join(phrase[:valid])
                if phrase in phrase_list:
                    tokens.append(phrase)
                else:
                    match = get_close_matches(phrase, phrase_list, n=1, cutoff=0)[0]
                    if match:
                        tokens.append(match)
                    else:
                        print("WARNING: No match found in phrase_list. This should never happen...")
            else:
                #short_word = all_tokens[idx].lower().split("'")[0]
                #if short_word in current_lookup:
                #    tokens.append(short_word)
                #else:
                try:
                    self.excluded[all_tokens[idx]] += 1
                except:
                    self.excluded[all_tokens[idx]] = 1

            idx += max(valid,1)
        
        return tokens
        
        
    
        
        
        