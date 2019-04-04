import re

from tools.tokenizer_util import separator_token, separator_token_replacement, number_token, iterate_tokens, TokenizerBase

def process_urls(info, runvars):
    text = runvars['document']['text']
    tokens = text.split()
    tokens = [token for token in tokens if not token.startswith('http')]
    runvars['document']['text'] = ' '.join(tokens)
    runvars['urls'] = []

def split(info, runvars):
    text = runvars['document']['text']
    text = text.replace(separator_token,separator_token_replacement)
    text = text.replace("-"," - ")
    runvars['tokens'] = text.split()

def lowercase_word(word):
    return word.lower()

def lowercase(info, runvars):
    if info['token_info']['lowercase']:
        iterate_tokens(runvars['tokens'], lowercase_word)

def split_numbers_word(word):
    words = []
    current_word = word[0]
    current_word_isdecimal = current_word.isdecimal()
    ignore_in_decimal = [",","."]
    ignore_count = 0 # counts how many consecutive ignore_in_decimal characters have appeared
    for char in word[1:]:
        if char.isdecimal() != current_word_isdecimal:
            if current_word_isdecimal and char in ignore_in_decimal and ignore_count == 0:
                ignore_count += 1
                current_word += char
            else:
                if ignore_count:
                    current_word = current_word[:-ignore_count]
                    ignore_count = 0
                words.append(current_word)
                current_word = char
                current_word_isdecimal = current_word.isdecimal()
        else:
            ignore_count = 0
            current_word += char
    
    if ignore_count:
        current_word = current_word[:-ignore_count]
    words.append(current_word)
    return words

def split_numbers(info, runvars):
    if info['token_info']['numbers_split']:
        iterate_tokens(runvars['tokens'], split_numbers_word)

re_number_only_single = re.compile("^(\d+)[\.,](\d+)$")
re_word_single_apostrophe = re.compile("^[^']+'[^']{1,3}$")

def remove_nonalnum_word(word):
    if word.isalnum():
        return word
    
    if re_number_only_single.match(word):
        return word
    elif re_word_single_apostrophe.match(word):
        parts = word.split("'")
        part_left = ''.join([char for char in parts[0] if char.isalnum()])
        part_right = ''.join([char for char in parts[1] if char.isalnum()])
        return "'".join([part_left, part_right])
        
    new_word = [char for char in word if char.isalnum()]
    return ''.join(new_word)

def remove_nonalnum(info, runvars):
    iterate_tokens(runvars['tokens'], remove_nonalnum_word)
    
def remove_nonascii_word(word):
    return word.encode('ascii',errors='ignore').decode()

def remove_nonascii(info, runvars):
    if info['token_info']["ascii_only"]:
        iterate_tokens(runvars['tokens'], remove_nonascii_word)
        
re_number_single = re.compile("[0-9]")
def _replace_numbers(word):
    return re_number_single.sub(number_token, word)

re_number_complete = re.compile("([0-9][0-9\.,]*)|([0-9\.,]*[0-9])")
def _replace_numbers_single(word):
    return re_number_complete.sub(number_token, word)

re_number_only_single = re.compile("^(\d+)[\.,](\d+)$")
def _replace_numbers_drop(word):
    return re_number_complete.sub("", word)

_replace_numbers_selector = {
    'replace': _replace_numbers,
    'replace_single': _replace_numbers_single,
    'drop': _replace_numbers_drop
}

def replace_numbers(info, runvars):
    numbers = info['token_info']["numbers"]
    if numbers == "keep":
        pass
    else:
        iterate_tokens(runvars['tokens'], _replace_numbers_selector[numbers])
      
def filter_stopwords_word(token):
    if token.lower() in ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 
                 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 
                 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 
                 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 
                 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 
                 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 
                 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 
                 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 
                 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 
                 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 
                 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 
                 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 
                 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 
                 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 
                 'was', 'here', 'than']:
        return '<STOPWORD>'
    return token
    
def filter_stopwords(info, runvars):
    iterate_tokens(runvars['tokens'], filter_stopwords_word)
      
class DefaultTokenizer(TokenizerBase):
    
    def __init__(self, info = None):
        if info is None:
            info = {'token_info': {"numbers": "replace",
                                   "numbers_split": False,
                                   "urls": "replace",
                                   "lowercase": False,
                                   "ascii_only": False,
                                   "remove_accents": False}}
        super().__init__(info)
        
    def tokenize(self, text, *args):
        runvars = {'document': {'text': text}}
        
        process_urls(self.info, runvars)
        split(self.info, runvars)
        lowercase(self.info, runvars)
        split_numbers(self.info, runvars)
        remove_nonalnum(self.info, runvars)
        remove_nonascii(self.info, runvars)
        replace_numbers(self.info, runvars)
        filter_stopwords(self.info, runvars)
        
        return runvars['tokens']
 