from tokens import Token, TokenKind, KEYWORDS, OPS, DELIMS, WHITESPACE


class Lexer:
    def __init__(self, src: str):
        self.src = src
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    # Cursor management

    def at_end(self) -> bool:
        return self.pos >= len(self.src)

    def peek(self, offset: int = 0) -> str:
        index = self.pos + offset

        if index < 0 or index >= len(self.src):
            return ""

        return self.src[index]

    def peeks(self, length: int = 1) -> str:
        return self.src[self.pos:self.pos + length]

    def advance(self, count: int = 1) -> str:
        consumed = ""

        for _ in range(count):
            if self.at_end():
                break

            char = self.src[self.pos]
            self.pos += 1
            consumed += char

            if char == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

        return consumed

    # Lexical grammar

    def is_letter(self, char: str) -> bool:
        return "a" <= char <= "z" or "A" <= char <= "Z"

    def is_digit(self, char: str) -> bool:
        return "0" <= char <= "9"

    def is_id_start(self, char: str) -> bool:
        return self.is_letter(char) or char == "_"

    def is_id_part(self, char: str) -> bool:
        return self.is_id_start(char) or self.is_digit(char)

    def is_id(self, lexeme: str) -> bool:
        if not lexeme:
            return False

        if not self.is_id_start(lexeme[0]):
            return False

        for char in lexeme[1:]:
            if not self.is_id_part(char):
                return False

        return True

    def is_int(self, lexeme: str) -> bool:
        if not lexeme:
            return False

        for char in lexeme:
            if not self.is_digit(char):
                return False

        return True

    def is_bool(self, lexeme: str) -> bool:
        return lexeme.lower() in ("true", "false")

    def is_keyword(self, lexeme: str) -> bool:
        return (
            lexeme.lower() in KEYWORDS
            and not self.is_bool(lexeme)
        )

    def is_op(self, lexeme: str) -> bool:
        return lexeme in OPS

    def is_delim(self, lexeme: str) -> bool:
        return lexeme in DELIMS

    def is_whitespace(self, char: str) -> bool:
        return char in WHITESPACE

    # Lexeme extraction

    def read_id(self) -> str:
        start = self.pos

        while self.is_id_part(self.peek()):
            self.advance()

        return self.src[start:self.pos]

    def read_int(self) -> str:
        start = self.pos

        while self.is_digit(self.peek()):
            self.advance()

        return self.src[start:self.pos]

    def read_symbol(self) -> str:
        max_length = max(
            max(map(len, OPS), default=0),
            max(map(len, DELIMS), default=0)
        )

        for length in range(max_length, 0, -1):
            lexeme = self.peeks(length)

            if len(lexeme) != length:
                continue

            if self.is_op(lexeme) or self.is_delim(lexeme):
                return self.advance(length)

        raise LexerError(
            f"Unexpected character '{self.peek()}'",
            self.src,
            self.line,
            self.col
        )

    # Token classification

    def classify(self, lexeme: str) -> TokenKind:
        normalized = lexeme.lower()

        if self.is_keyword(lexeme):
            return KEYWORDS[normalized]

        if self.is_bool(lexeme):
            return (
                TokenKind.TRUE
                if normalized == "true"
                else TokenKind.FALSE
            )

        if self.is_id(lexeme):
            return TokenKind.IDENTIFIER

        if self.is_int(lexeme):
            return TokenKind.INTEGER

        if self.is_op(lexeme):
            return OPS[lexeme]

        if self.is_delim(lexeme):
            return DELIMS[lexeme]

        raise LexerError(
            f"Invalid lexeme '{lexeme}'",
            self.src,
            self.line,
            self.col
        )

    # Tokenization

    def tokenize(self) -> list[Token]:
        while not self.at_end():
            char = self.peek()

            if self.is_whitespace(char):
                self.advance()
                continue

            line = self.line
            col = self.col

            if self.is_id_start(char):
                lexeme = self.read_id()

            elif self.is_digit(char):
                lexeme = self.read_int()

            else:
                lexeme = self.read_symbol()

            kind = self.classify(lexeme)

            self.tokens.append(
                Token(kind, lexeme, line, col)
            )

        self.tokens.append(
            Token(TokenKind.EOF, "", self.line, self.col)
        )

        return self.tokens


class LexerError(Exception):
    def __init__(
        self,
        message: str,
        src: str,
        line: int,
        col: int
    ):
        lines = src.split("\n")
        src_line = lines[line - 1]

        pointer = " " * (col - 1) + "^"

        super().__init__(
            f"LexerError at {line}:{col}: {message}\n"
            f"{src_line}\n"
            f"{pointer}"
        )
