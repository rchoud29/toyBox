from dataclasses import dataclass, field
from typing import List, Union

from tokens import Token

class ASTNode:
    pass

@dataclass
class NumNode(ASTNode):
    val: Union[int, float]

    def __repr__(self):
        return f"NumNode({self.val})"

@dataclass
class BoolNode(ASTNode):
    val: bool

    def __repr(self):
        if self.val == 0:
            return f"BoolNode({self.val})"

@dataclass
class IdNode(ASTNode):
    name: str

    def __repr__(self):
        return f"Node({self.name})"

@dataclass
class CompOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def __repr__(self):
        return f"CompOpNode({self.a} {self.op} {self.b})"

@dataclass
class BoolOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def __repr__(self):
        return f"BoolOpNode({self.a} {self.op} {self.b})"

@dataclass
class BinOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def __repr__(self):
        return f"BinOpNode({self.a} {self.op} {self.b})"

@dataclass
class PrintNode(ASTNode):
    expr: ASTNode 

    def __repr__(self):
        return f"PrintNode({self.expr})"

@dataclass
class AssignNode(ASTNode):
    name: Token
    expr: ASTNode

    def __repr__(self):
        return f"AssignNode({self.name} = {self.expr})"

@dataclass
class ForLoop(ASTNode):
    assignments: List[ASTNode]
    conds: List[ASTNode]
    blocks: List[ASTNode]
    a: ASTNode
    c: ASTNode = None
    
    def __repr__(self):
        return f"ForLoop()"

@dataclass
class WhileNode(ASTNode):
    cond: BoolNode
    a: ASTNode
    c: ASTNode = None

    def __repr__(self):
        return f"IfNode({self.cond}, {self.a}, {self.c})"

@dataclass
class IfNode(ASTNode):
    cond: BoolNode
    a: ASTNode
    b: ASTNode = None
    c: ASTNode = None

    def __repr__(self):
        return f"IfNode({self.cond}, {self.a}, {self.b}, {self.c})"

@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

    def __repr__(self):
        return f"BlockNode({self.statements})"

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

    def __repr__(self):
        return f"ProgramNode({self.statements!r})"
