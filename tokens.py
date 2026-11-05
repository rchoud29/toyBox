from enum import Enum, auto

class TokenType(Enum):
    # Literals & Identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()

    # Keywords
    TRUE = auto()
    FALSE = auto()
    PRINT = auto()
    IF = auto()
    ELSE = auto()
    FINALLY = auto()
    WHILE = auto()
    FOR = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()     # =
    EQ = auto()         # ==
    NEQ = auto()        # !=
    LESS = auto()       # <
    LEQ = auto()        # <=
    GREATER = auto()    # >
    GEQ = auto()        # >=
    AND = auto()        # &&
    BAND = auto()       # &
    OR = auto()         # ||
    BOR = auto()        # |
    NOT = auto()        # !

    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    SEMICOLON = auto()  # ;
    COMMA = auto()      # ,

    # Control
    EOF = auto()


class Token:
    def __init__(self, type_: TokenType, val=None, line: int = 1, col: int = 1, pos: int = 0):
        self.type = type_
        self.val = val
        self.line = line
        self.col = col
        self.pos = pos

    def __repr__(self):
        if self.val is not None:
            return f"Token({self.type.name}, {self.val!r})"
        return f"Token({self.type.name})"
