from enum import Enum, auto

class TokenType(Enum):
    # Literals & Identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Keywords
    PRINT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()      # =
    EQ = auto()          # ==
    NEQ = auto()         # !=
    LESS = auto()        # <
    LEQ = auto()         # <=
    GREATER = auto()     # >
    GEQ = auto()         # >=
    AND = auto()         # &&
    OR = auto()          # ||

    # Delimiters
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    SEMICOLON = auto()   # ;

    # Control
    EOF = auto()


class Token:
    def __init__(self, type_: TokenType, val=None):
        self.type = type_
        self.val = val

    def __repr__(self):
        if self.val is not None:
            return f"Token({self.type.name}, {self.val!r})"
        return f"Token({self.type.name})"
