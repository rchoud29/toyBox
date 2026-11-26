from __future__ import annotations
from dataclasses import dataclass
from tokens import TokenKind


# Base nodes

class Node:
    pass


class Expression(Node):
    pass


class Statement(Node):
    pass


# Types

@dataclass
class Type(Node):
    name: str


# Expressions

@dataclass
class Integer(Expression):
    value: int


@dataclass
class Boolean(Expression):
    value: bool


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class BinaryExpression(Expression):
    left: Expression
    op: TokenKind
    right: Expression


@dataclass
class UnaryExpression(Expression):
    op: TokenKind
    operand: Expression


@dataclass
class Cast(Expression):
    type: Type
    value: Expression


@dataclass
class Call(Expression):
    name: str
    arguments: list[Expression]


# Statements

@dataclass
class Declaration(Statement):
    name: str
    type: Type
    value: Expression


@dataclass
class Assignment(Statement):
    name: str
    value: Expression


@dataclass
class Return(Statement):
    value: Expression | None


@dataclass
class Block(Node):
    statements: list[Statement]


@dataclass
class If(Statement):
    condition: Expression
    body: Block
    else_body: Block | If | None = None


@dataclass
class While(Statement):
    condition: Expression
    body: Block


@dataclass
class CallStatement(Statement):
    call: Call


# Functions

@dataclass
class Parameter(Node):
    name: str
    type: Type


@dataclass
class Function(Node):
    name: str
    parameters: list[Parameter]
    return_type: Type
    body: Block


# Program

@dataclass
class Program(Node):
    functions: list[Function]
