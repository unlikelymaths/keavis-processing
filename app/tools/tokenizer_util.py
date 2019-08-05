
separator_token = ";"
separator_token_replacement = ","
number_token = "#"

def split_tokens(token_str):
    return token_str.split(separator_token)
    
def join_tokens(tokens):
    return separator_token.join(tokens)

    
def iterate_tokens(tokens, func):
    i = 0
    while i < len(tokens):
        result = func(tokens[i])
        if isinstance(result, str):
            if len(result) == 0:
                del tokens[i]
            else:
                tokens[i] = result
                i += 1
        elif result is None:
            del tokens[i]
        elif isinstance(result, list):
            if len(result) == 0:
                del tokens[i]
            else:
                tokens[i] = result[0]
                i += 1
                for token in result[1:]:
                    tokens.insert(i,token)
                    i += 1
                    
class TokenizerBase():
    def __init__(self, info = {}):
        self.info = info
        self.initialize()
        
    def initialize(self):
        pass
    
    def tokenize(text):
        return text.split()