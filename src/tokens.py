from enum import Enum, auto
from dataclasses import dataclass
class TokenKind(Enum):
    FN=auto(); DF=auto(); ST=auto(); RETURN=auto(); IF=auto(); ELSE=auto(); WHILE=auto()
    INTEGER=auto(); TRUE=auto(); FALSE=auto(); IDENTIFIER=auto()
    PLUS=auto(); MINUS=auto(); STAR=auto(); SLASH=auto(); PERCENT=auto()
    ASSIGN=auto(); EQ=auto(); NEQ=auto(); LT=auto(); GT=auto(); LTE=auto(); GTE=auto(); NOT=auto()
    LPAREN=auto(); RPAREN=auto(); LBRACE=auto(); RBRACE=auto(); COLON=auto(); SEMICOLON=auto(); COMMA=auto(); EOF=auto()
KEYWORDS={s:TokenKind[s.upper()] for s in 'fn df st return if else while true false'.split()}
OPS=dict(zip('+ - * / % = == != < > <= >= !'.split(), [TokenKind[x] for x in 'PLUS MINUS STAR SLASH PERCENT ASSIGN EQ NEQ LT GT LTE GTE NOT'.split()]))
DELIMS=dict(zip('(){}:;,',[TokenKind[x] for x in 'LPAREN RPAREN LBRACE RBRACE COLON SEMICOLON COMMA'.split()]))
WHITESPACE=set(' \t\n\r')
@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    column: int
