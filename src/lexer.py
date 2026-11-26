from tokens import *
class LexerError(Exception): pass
class Lexer:
    def __init__(self, src):
        self.src=src; self.pos=0; self.line=1; self.col=1
    def at_end(self): return self.pos>=len(self.src)
    def peek(self, offset=0):
        i=self.pos+offset
        return self.src[i] if 0<=i<len(self.src) else ''
    def peeks(self,length=1): return self.src[self.pos:self.pos+length]
    def advance(self,count=1):
        text=self.peeks(count)
        for c in text:
            self.pos+=1
            if c=='\n': self.line+=1; self.col=1
            else: self.col+=1
        return text
    def is_letter(self,c): return 'a'<=c<='z' or 'A'<=c<='Z'
    def is_digit(self,c): return '0'<=c<='9'
    def is_id_start(self,c): return self.is_letter(c) or c=='_'
    def is_id_part(self,c): return self.is_id_start(c) or self.is_digit(c)
    def is_id(self,s): return bool(s) and self.is_id_start(s[0]) and all(map(self.is_id_part,s[1:]))
    def is_int(self,s): return bool(s) and all(map(self.is_digit,s))
    def is_bool(self,s): return s.lower() in ('true','false')
    def is_keyword(self,s): return s.lower() in KEYWORDS and not self.is_bool(s)
    def is_op(self,s): return s in OPS
    def is_delim(self,s): return s in DELIMS
    def is_whitespace(self,s): return s in WHITESPACE
    def classify(self,s):
        if self.is_keyword(s) or self.is_bool(s): return KEYWORDS[s.lower()]
        if self.is_id(s): return TokenKind.IDENTIFIER
        if self.is_int(s): return TokenKind.INTEGER
        if self.is_op(s): return OPS[s]
        if self.is_delim(s): return DELIMS[s]
        raise LexerError(f'Invalid token {s!r}')
    def tokenize(self):
        tokens=[]
        while not self.at_end():
            c=self.peek(); start=self.pos; line=self.line; col=self.col
            if self.is_whitespace(c): self.advance(); continue
            if self.is_id_start(c):
                while self.is_id_part(self.peek()): self.advance()
            elif self.is_digit(c):
                while self.is_digit(self.peek()): self.advance()
            else:
                for n in range(max(map(len,OPS|DELIMS)),0,-1):
                    s=self.peeks(n)
                    if len(s)==n and (self.is_op(s) or self.is_delim(s)):
                        self.advance(n); break
                else: raise LexerError(f'{line}:{col}: unexpected {c!r}')
            s=self.src[start:self.pos]; tokens.append(Token(self.classify(s),s,line,col))
        return tokens+[Token(TokenKind.EOF,'',self.line,self.col)]
