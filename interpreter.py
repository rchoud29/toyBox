from ASTNode import (
    ASTNode,
    ProgramNode,
    AssignNode,
    PrintNode,
    BinOpNode,
    BoolOpNode,
    NumNode,
    IdNode,
)
from tokens import TokenType, Token


class Interpreter:
    def __init__(self):
        self.env = {}

    def interpret(self, node: ASTNode):
        return self.visit(node)

    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")

    def visit_ProgramNode(self, node: ProgramNode):
        result = None
        for statement in node.statements:
            result = self.visit(statement)
        return result

    def visit_AssignNode(self, node: AssignNode):
        value = self.visit(node.expr)
        # Handles whether node.name is a Token instance or a string
        var_name = node.name.value if hasattr(node.name, 'value') else str(node.name)
        self.env[var_name] = value
        return value

    def visit_PrintNode(self, node: PrintNode):
        value = self.visit(node.expr)
        print(value)
        return value

    def visit_NumNode(self, node: NumNode):
        return node.val

    def visit_IdNode(self, node: IdNode):
        var_name = node.name.value if hasattr(node.name, 'value') else str(node.name)
        if var_name in self.env:
            return self.env[var_name]
        raise NameError(f"Undefined variable '{var_name}'")

    def visit_BinOpNode(self, node: BinOpNode):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)
        op_type = node.op.type if hasattr(node.op, 'type') else node.op

        if op_type in (TokenType.PLUS, '+'):
            return left_val + right_val
        elif op_type in (TokenType.MINUS, '-'):
            return left_val - right_val
        elif op_type in (TokenType.STAR, '*'):
            return left_val * right_val
        elif op_type in (TokenType.SLASH, '/'):
            if right_val == 0:
                raise ZeroDivisionError("Division by zero")
            return left_val / right_val
        else:
            raise ValueError(f"Unsupported binary operator: {node.op}")

    def visit_BoolOpNode(self, node: BoolOpNode):
        op_type = node.op.type if hasattr(node.op, 'type') else node.op

        # Short-circuit logic operators
        if op_type in (TokenType.AND, '&&'):
            return bool(self.visit(node.left) and self.visit(node.right))
        elif op_type in (TokenType.OR, '||'):
            return bool(self.visit(node.left) or self.visit(node.right))

        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if op_type in (TokenType.EQ, '=='):
            return left_val == right_val
        elif op_type in (TokenType.NEQ, '!='):
            return left_val != right_val
        elif op_type in (TokenType.LESS, '<'):
            return left_val < right_val
        elif op_type in (TokenType.LEQ, '<='):
            return left_val <= right_val
        elif op_type in (TokenType.GREATER, '>'):
            return left_val > right_val
        elif op_type in (TokenType.GEQ, '>='):
            return left_val >= right_val
        else:
            raise ValueError(f"Unsupported comparison operator: {node.op}")
