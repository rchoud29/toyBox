from dataclasses import dataclass, field, fields, is_dataclass
from typing import List, Union, Optional
from tokens import Token


class ASTNode:
    def code(self) -> str:
        """Returns the human-readable string representation of the node."""
        return ""

    def tree(self, level: int = 0) -> str:
        """Generates a tab-indented tree displaying constructor form and human-readable form."""
        indent = "\t" * level
        cls_name = self.__class__.__name__

        if not is_dataclass(self):
            return f"{indent}{self}"

        meta = []
        children = []

        # Separate primitive attributes from AST child nodes and lists
        for f in fields(self):
            val = getattr(self, f.name)
            if val is None:
                continue
            if isinstance(val, ASTNode) or (isinstance(val, list) and any(isinstance(x, ASTNode) for x in val)):
                children.append((f.name, val))
            elif isinstance(val, Token):
                meta.append(f"{f.name}={val.val!r}")
            else:
                meta.append(f"{f.name}={val!r}")

        constructor_str = f"{cls_name}({', '.join(meta)})" if meta else f"{cls_name}()"
        human_code = self.code()
        human_str = f"  =>  {human_code}" if human_code else ""

        lines = [f"{indent}{constructor_str}{human_str}"]

        for fname, child in children:
            if isinstance(child, list):
                lines.append(f"{indent}\t{fname}:")
                for item in child:
                    if isinstance(item, ASTNode):
                        lines.append(item.tree(level + 2))
                    else:
                        lines.append(f"{indent}\t\t{item}")
            elif isinstance(child, ASTNode):
                lines.append(f"{indent}\t{fname}:")
                lines.append(child.tree(level + 2))

        return "\n".join(lines)

    def __repr__(self):
        return self.tree()


# --- Value & Expression Nodes ---

@dataclass(repr=False)
class NumNode(ASTNode):
    val: Union[int, float]

    def code(self):
        return str(self.val)


@dataclass(repr=False)
class BoolNode(ASTNode):
    val: bool

    def code(self):
        return str(self.val).lower()


@dataclass(repr=False)
class IdNode(ASTNode):
    name: str

    def code(self):
        return str(self.name)


@dataclass(repr=False)
class BinOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def code(self):
        op_str = self.op.value if hasattr(self.op, "value") else str(self.op)
        return f"({self.a.code()} {op_str} {self.b.code()})"


@dataclass(repr=False)
class CompOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def code(self):
        op_str = self.op.value if hasattr(self.op, "value") else str(self.op)
        return f"({self.a.code()} {op_str} {self.b.code()})"


@dataclass(repr=False)
class BoolOpNode(ASTNode):
    op: Token
    a: ASTNode
    b: ASTNode

    def code(self):
        op_str = self.op.value if hasattr(self.op, "value") else str(self.op)
        return f"({self.a.code()} {op_str} {self.b.code()})"


# --- Statement & Control Flow Nodes ---

@dataclass(repr=False)
class PrintNode(ASTNode):
    expr: ASTNode

    def code(self):
        return f"print({self.expr.code()});"


@dataclass(repr=False)
class AssignNode(ASTNode):
    name: Token
    expr: ASTNode

    def code(self):
        var_name = self.name.value if hasattr(self.name, "value") else str(self.name)
        return f"{var_name} = {self.expr.code()};"


@dataclass(repr=False)
class IfNode(ASTNode):
    cond: ASTNode
    a: ASTNode
    b: Optional[ASTNode] = None
    c: Optional[ASTNode] = None

    def code(self):
        return f"if ({self.cond.code()})"


@dataclass(repr=False)
class WhileNode(ASTNode):
    cond: ASTNode
    a: ASTNode
    c: Optional[ASTNode] = None

    def code(self):
        return f"while ({self.cond.code()})"


@dataclass(repr=False)
class ForLoop(ASTNode):
    assignments: List[ASTNode]
    conds: List[ASTNode]
    blocks: List[ASTNode]
    a: ASTNode
    c: Optional[ASTNode] = None

    def code(self):
        return "for (...)"


# --- Structural Nodes ---

@dataclass(repr=False)
class BlockNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

    def code(self):
        return f"{{ ... {len(self.statements)} statement(s) ... }}"


@dataclass(repr=False)
class ProgramNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

    def code(self):
        return f"<Program: {len(self.statements)} statement(s)>"
