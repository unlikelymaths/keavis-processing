import logging
from os.path import isfile
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
from gensim.models import KeyedVectors

from tools.s3 import intermediate_bucket

class Word2VecFilter():
    exists_token = "###WORD_EXISTS###"

    def __init__(self, vocab):
        self.lookup = {}
        for token in vocab:
            words = token.split('_')
            if '' in words or len(words) == 0:
                continue
            current_lookup = self.lookup
            for word in words:
                lower_word = word.lower()
                if not lower_word in current_lookup:
                    current_lookup[lower_word] = {}
                current_lookup = current_lookup[lower_word]
            if Word2VecFilter.exists_token not in current_lookup:
                current_lookup[Word2VecFilter.exists_token] = token

    def filter(self, all_tokens):
        idx = 0
        tokens = []
        while idx < len(all_tokens):
            phrase = None
            currentidx = idx
            valid = 0
            current_lookup = self.lookup
            while currentidx < len(all_tokens) and all_tokens[currentidx].lower() in current_lookup:
                current_lookup = current_lookup[all_tokens[currentidx].lower()]
                if Word2VecFilter.exists_token in current_lookup:
                    phrase = current_lookup[Word2VecFilter.exists_token]
                    valid = valid + 1
                currentidx = currentidx + 1
            if phrase is not None:
                tokens.append(phrase)
            idx += max(valid,1)
        return tokens

class Word2vecModel():
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._model = None
        self._vector_size = None
        self._embedding_function = None
        self._vocab = None
        self._filter = None

        self.embedding_filename = '/data/embedding/word2vec.bin'
        self.embedding_key = 'embedding/word2vec.bin'

    @property
    def model(self):
        if self._model is None:
            self._model = self._load_model()
        return self._model

    @property
    def vector_size(self):
        if self._vector_size is None:
            self._vector_size = self.model.wv.vector_size
        return self._vector_size

    @property
    def embedding_function(self):
        if self._embedding_function is None:
            self._embedding_function = self._load_embedding_function()
        return self._embedding_function

    @property
    def vocab(self):
        if self._vocab is None:
            self._vocab = [str(token) for token in self.model.vocab]
        return self._vocab

    @property
    def filter(self):
        if self._filter is None:
            self.vocab
            self._logger.debug('Creating embedding filter')
            self._filter = Word2VecFilter(self.vocab)
        return self._filter

    def _load_model(self):
        if not isfile(self.embedding_filename):
            self._logger.debug('Downloading embedding data ({})'
                         .format(self.embedding_filename))
            intermediate_bucket.download_file(self.embedding_key, 
                                              self.embedding_filename)
        self._logger.debug('Loading embedding data ({})'
                     .format(self.embedding_filename))
        return KeyedVectors.load_word2vec_format(
            self.embedding_filename, binary=True)

    def _load_embedding_function(self):
        wv = self.model.wv
        def embedding_function(token):
            try:
                return wv[token]
            except:
                raise OOVException('Word2vecModel',token)
        return embedding_function
