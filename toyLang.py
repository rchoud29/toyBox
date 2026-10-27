class ToyLang:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.token_feed = self.tokens()
        self.returned_tokens = []

    def raise_error(self, msg):
        raise ValueError(f'{self.pos}: {msg}')
    


    def islegal(self, char):
        allowed = {'(',')',';','\n',' ','_','<EOF>'}
        return bool(char) and (char.isalnum() or char in allowed)

    def ispunctuation(self, char):
        allowed = {'(',')',';'}
        return  char in allowed

    def is_identifier_start(self, char):
        allowed = {'_'}
        return char.isalpha() or char in allowed
    def is_identifier_part(self, char):
        allowed = {'_'}
        return char.isalpha() or char in allowed



    def next_token(self):
        if self.returned_tokens:
            token = self.returned_tokens.pop(0)
        else:
            try:
                token = next(self.token_feed)
            except StopIteration:
                token = None

        return token
    
    def return_token(self, token):
        if islegal(token):
            self.returned_tokens.append(token)



    def tokens(self):
        while self.pos < len(self.code):
            char = self.code[self.pos]
            start = self.pos

            if char.isspace():
                self.pos += 1
                continue

            if self.ispunctuation(char):
                yield ('punctuation', char)
                self.pos += 1
                continue

            if self.is_identifier_start(char):
                while self.pos < len(self.code) and \
                        self.is_identifier_part(self.code[self.pos]):
                    self.pos += 1
                yield ('identifier', self.code[start:self.pos])
                continue

            if char.isdigit():
                while self.pos < len(self.code) and \
                                 self.code[self.pos].isdigit():
                    self.pos += 1
                yield ('number', self.code[start:self.pos])
                continue
            
            self.raise_error(f"Unexpected character '{char}'")
