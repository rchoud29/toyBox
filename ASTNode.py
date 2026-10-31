from dataclasses import dataclass, field
from typing import List, Union

class ASTNode:
    pass

@dataclass
class NumNode(ASTNode):
    val: Union[int, float]

    def __repr__(self):
        return f"NumNode({self.value})"

@dataclass
class IdNode(ASTNode):
    name: str

    def __repr__(self):
        return f"Node({self.name})"

@dataclass
class BinOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"BinOpNode({self.left} {self.op} {self.right})"

@dataclass
class PrintNode(ASTNode):
    expr: ASTNode 

    def __repr__(self):
        return f"PrintNode({self.expr})"

@dataclass
class AssignNode(ASTNode):
    name: str
    expr: ASTNode

    def __repr__(self):
        return f"AssignNode({self.name} = {self.expr})"

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

    def __repr__(self):
        return f"ProgramNode({self.statements})"
