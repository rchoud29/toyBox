from tokens import TokenType, Token

KEYWORDS = {
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "finally": TokenType.FINALLY,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "print": TokenType.PRINT,
}

SYMBOLS = {
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,
    ';': TokenType.SEMICOLON,
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.STAR,
    '/': TokenType.SLASH,
    '<': TokenType.LESS,
    '>': TokenType.GREATER,
    ',': TokenType.COMMA
}

class Lexer:
    def __init__(self, code):
        self.code = code.lower()
        self.pos = 0
        self.token_feed = self.tokens()
        self.returned_tokens = []

    def raise_error(self, msg):
        raise ValueError(f"{self.pos}: {msg}")

    def peek(self):
        if (pos := self.pos + 1) < len(self.code):
            return self.code[pos]
        return None

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

            if char == '=':
                if self.peek() == '=':
                    self.pos += 2
                    yield Token(TokenType.EQ, "==")
                else: 
                    self.pos += 1
                    yield Token(TokenType.ASSIGN, char)
                continue

            if char == '!':
                if self.peek() == '=':
                    self.pos += 2
                    yield Token(TokenType.NEQ, '!=')
                else:
                    self.pos += 1
                    yield Token(TokenType.NOT, char)
                continue

            if char == '&':
                if self.peek() == '&':
                    self.pos += 2
                    yield Token(TokenType.AND, "&&")
                else:
                    self.pos += 1
                    yield Token(TokenType.BAND, '&')
                continue

            if char == '|':
                if self.peek() == '|':
                    self.pos += 2
                    yield Token(TokenType.OR, "||")
                else:
                    self.pos += 1
                    yield Token(TokenType.BOR, '|')
                continue

            if char == '<':
                if self.peek() == '=':
                    self.pos += 2
                    yield Token(TokenType.LEQ, '<=')
                else:
                    self.pos += 1
                    yield Token(TokenType.LESS, '<')
                continue

            if char == '>':
                if self.peek() == '=':
                    self.pos += 2
                    yield Token(TokenType.GEQ, '>=')
                else:
                    yield Token(TokenType.GREATER, '>')
                continue

            if char in SYMBOLS:
                self.pos += 1
                yield Token(SYMBOLS[char], char)
                continue

            if self.isidentifierstart(char):
                while self.pos < len(self.code) and \
                        self.isidentifierpart(self.code[self.pos]):
                    self.pos += 1
                val = self.code[start:self.pos]
                type = KEYWORDS.get(val, TokenType.IDENTIFIER)
                yield Token(type, val)
                continue

            if char.isdigit():
                while self.pos < len(self.code) and \
                                 self.code[self.pos].isdigit():
                    self.pos += 1
                yield Token(TokenType.NUMBER, int(self.code[start:self.pos]))
                continue

            self.raise_error(f"Unexpected character '{char}'")
            
        yield Token(TokenType.EOF)


