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
        self.code = code
        self.pos = 0
        self.line = 1
        self.col = 1
        self.token_feed = self.tokens()
        self.returned_tokens = []

    def raise_error(self, msg):
        raise ValueError(f"[{self.line}:{self.col} (pos {self.pos})]: {msg}")

    def peek(self):
        if (pos := self.pos + 1) < len(self.code):
            return self.code[pos]
        return None

    def advance(self, amount: int = 1):
        """Advances reader position while updating line and column counters."""
        for _ in range(amount):
            if self.pos < len(self.code):
                if self.code[self.pos] == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.pos += 1

    def isidentifierstart(self, char):
        allowed = {'_'}
        return char.isalpha() or char in allowed

    def isidentifierpart(self, char):
        allowed = {'_'}
        return char.isalnum() or char in allowed

    def next_token(self):
        if self.returned_tokens:
            return self.returned_tokens.pop()
        try:
            return next(self.token_feed)
        except StopIteration:
            return None
    
    def return_token(self, token):
        if token is not None:
            self.returned_tokens.append(token)

    def return_tokens(self, tokens):
        for token in tokens:
            self.return_token(token)

    def tokens(self):
        code_lower = self.code.lower()

        while self.pos < len(self.code):
            char = code_lower[self.pos]
            start_line, start_col, start_pos = self.line, self.col, self.pos

            if char.isspace():
                self.advance(1)
                continue

            if char == '=':
                if self.peek() == '=':
                    self.advance(2)
                    yield Token(TokenType.EQ, "==", start_line, start_col, start_pos)
                else: 
                    self.advance(1)
                    yield Token(TokenType.ASSIGN, char, start_line, start_col, start_pos)
                continue

            if char == '!':
                if self.peek() == '=':
                    self.advance(2)
                    yield Token(TokenType.NEQ, '!=', start_line, start_col, start_pos)
                else:
                    self.advance(1)
                    yield Token(TokenType.NOT, char, start_line, start_col, start_pos)
                continue

            if char == '&':
                if self.peek() == '&':
                    self.advance(2)
                    yield Token(TokenType.AND, "&&", start_line, start_col, start_pos)
                else:
                    self.advance(1)
                    yield Token(TokenType.BAND, '&', start_line, start_col, start_pos)
                continue

            if char == '|':
                if self.peek() == '|':
                    self.advance(2)
                    yield Token(TokenType.OR, "||", start_line, start_col, start_pos)
                else:
                    self.advance(1)
                    yield Token(TokenType.BOR, '|', start_line, start_col, start_pos)
                continue

            if char == '<':
                if self.peek() == '=':
                    self.advance(2)
                    yield Token(TokenType.LEQ, '<=', start_line, start_col, start_pos)
                else:
                    self.advance(1)
                    yield Token(TokenType.LESS, '<', start_line, start_col, start_pos)
                continue

            if char == '>':
                if self.peek() == '=':
                    self.advance(2)
                    yield Token(TokenType.GEQ, '>=', start_line, start_col, start_pos)
                else:
                    self.advance(1)
                    yield Token(TokenType.GREATER, '>', start_line, start_col, start_pos)
                continue

            if char in SYMBOLS:
                self.advance(1)
                yield Token(SYMBOLS[char], char, start_line, start_col, start_pos)
                continue

            if self.isidentifierstart(char):
                start_idx = self.pos
                while self.pos < len(self.code) and self.isidentifierpart(code_lower[self.pos]):
                    self.advance(1)
                val = code_lower[start_idx:self.pos]
                if val in ("true", "false"):
                    yield Token(TokenType.BOOLEAN, val == "true", start_line, start_col, start_pos)
                else:
                    type_ = KEYWORDS.get(val, TokenType.IDENTIFIER)
                    yield Token(type_, val, start_line, start_col, start_pos)
                continue

            if char.isdigit():
                start_idx = self.pos
                while self.pos < len(self.code) and code_lower[self.pos].isdigit():
                    self.advance(1)
                yield Token(TokenType.NUMBER, int(code_lower[start_idx:self.pos]), start_line, start_col, start_pos)
                continue

            self.raise_error(f"Unexpected character '{char}'")
            
        yield Token(TokenType.EOF, None, self.line, self.col, self.pos)
