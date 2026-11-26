from enum import Enum, auto
from dataclasses import dataclass




class TokenKind(Enum):
    # Keywords
    FN = auto()
    DF = auto()
    ST = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()

    # Literals
    INTEGER = auto()
    TRUE = auto()
    FALSE = auto()

    # Identifiers
    IDENTIFIER = auto()

    # Arithmetic
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    # Comparison and assignment
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    NOT = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()

    EOF = auto()

KEYWORDS = {
    "fn": TokenKind.FN,
    "df": TokenKind.DF,
    "st": TokenKind.ST,
    "return": TokenKind.RETURN,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
}

OPS = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "%": TokenKind.PERCENT,

    "=": TokenKind.ASSIGN,
    "==": TokenKind.EQ,
    "!=": TokenKind.NEQ,
    "<": TokenKind.LT,
    ">": TokenKind.GT,
    "<=": TokenKind.LTE,
    ">=": TokenKind.GTE,
    "!": TokenKind.NOT,
}

DELIMS = {
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    ":": TokenKind.COLON,
    ";": TokenKind.SEMICOLON,
    ",": TokenKind.COMMA,
}

WHITESPACE = {
    " ",
    "\t",
    "\n",
    "\r",
}

@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    column: int
