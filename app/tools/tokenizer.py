import re

# numbers
number_token = "#"
# replace all whitespaces
_re_whitespace = re.compile('[\s]+', re.UNICODE)
# remove urls
_re_url = re.compile('(http://[^\s]+)|(https://[^\s]+)|(www\.[^\s]+)')
# replace numbers
_re_decimal = re.compile('\d', re.UNICODE)
# split string into substrings of non alphanumeric characters
_re_breaking = re.compile('[^\w\s\'\’#]+', re.UNICODE)

class Tokenizer():
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def tokenize(self, text):
        self.text = text
        self.prepare()
        self.replace_numbers()
        self.split_text()
        self.split_subtexts()
        self.build_tokens()
        return self.tokens

    def prepare(self):
        self.text = self.text.lower()
        self.text = self.text.replace(number_token, ' ')
        self.text, count = _re_url.subn(' ', self.text)
        self.text, count = _re_whitespace.subn(' ', self.text)

    def replace_numbers(self):
        self.text, count = _re_decimal.subn('#', self.text)

    def split_text(self):
        self.subtexts = _re_breaking.split(self.text)

    def split_subtexts(self):
        self.tokenlists = [subtext.split()
                        for subtext in self.subtexts
                        if len(subtext) > 0]

    def build_tokens(self):
        self.tokens = []
        for tokenlist in self.tokenlists:
            self.tokens = self.tokens + self.embedding_model.filter.filter(tokenlist)
