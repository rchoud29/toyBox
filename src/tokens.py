from enum import Enum, auto
from dataclasses import dataclass


class TokenKind(Enum):
    FN = auto()
    DF = auto()
    ST = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    INTEGER = auto()
    TRUE = auto()
    FALSE = auto()
    IDENTIFIER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    EOF = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()
    PERCENT_ASSIGN = auto()
    INCREMENT = auto()
    DECREMENT = auto()

KEYWORDS = {
    'fn': TokenKind.FN,
    'df': TokenKind.DF,
    'st': TokenKind.ST,
    'return': TokenKind.RETURN,
    'if': TokenKind.IF,
    'else': TokenKind.ELSE,
    'while': TokenKind.WHILE,
    'for': TokenKind.FOR,
    'true': TokenKind.TRUE,
    'false': TokenKind.FALSE,
}

OPS = {
    '+': TokenKind.PLUS,
    '-': TokenKind.MINUS,
    '*': TokenKind.STAR,
    '/': TokenKind.SLASH,
    '%': TokenKind.PERCENT,
    '=': TokenKind.ASSIGN,
    '==': TokenKind.EQ,
    '!=': TokenKind.NEQ,
    '<': TokenKind.LT,
    '>': TokenKind.GT,
    '<=': TokenKind.LTE,
    '>=': TokenKind.GTE,
    '!': TokenKind.NOT,
    '+=': TokenKind.PLUS_ASSIGN,
    '-=': TokenKind.MINUS_ASSIGN,
    '*=': TokenKind.STAR_ASSIGN,
    '/=': TokenKind.SLASH_ASSIGN,
    '%=': TokenKind.PERCENT_ASSIGN,
    '++': TokenKind.INCREMENT,
    '--': TokenKind.DECREMENT,
}

DELIMS = {
    '(': TokenKind.LPAREN,
    ')': TokenKind.RPAREN,
    '{': TokenKind.LBRACE,
    '}': TokenKind.RBRACE,
    ':': TokenKind.COLON,
    ';': TokenKind.SEMICOLON,
    ',': TokenKind.COMMA,
}

WHITESPACE = set(' \t\n\r')


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    column: int
