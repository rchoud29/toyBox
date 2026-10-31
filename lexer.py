class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.token_feed = self.tokens()
        self.returned_tokens = []

    def raise_error(self, msg):
        raise ValueError(f"{self.pos}: {msg}")

    def ispunctuation(self, char):
        allowed = {'(',')',';','='}
        return  char in allowed

    def isoperator(self, char):
        allowed = {'+', '-', '*', '/'}
        return char in allowed

    def isidentifierstart(self, char):
        allowed = {'_'}
        return char.isalpha() or char in allowed

    def isidentifierpart(self, char):
        allowed = {'_'}
        return char.isalnum() or char in allowed

    def next_token(self):
        if self.returned_tokens:
            token = self.returned_tokens.pop()
        else:
            try:
                token = next(self.token_feed)
            except StopIteration:
                token = None

        return token
    
    def return_token(self, token):
        if token is not None:
            self.returned_tokens.append(token)

    def return_tokens(self, tokens):
        for token in tokens:
            self.return_token(token)

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
            
            if self.isoperator(char):
                yield ('operator', char)
                self.pos += 1
                continue

            if self.isidentifierstart(char):
                while self.pos < len(self.code) and \
                        self.isidentifierpart(self.code[self.pos]):
                    self.pos += 1
                yield ('identifier', self.code[start:self.pos])
                continue

            if char.isdigit():
                while self.pos < len(self.code) and \
                                 self.code[self.pos].isdigit():
                    self.pos += 1
                yield ('number', int(self.code[start:self.pos]))
                continue

            self.raise_error(f"Unexpected character '{char}'")
