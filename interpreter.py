from ASTNode import (
    ProgramNode,
    AssignNode,
    PrintNode,
    CompOpNode,
    BoolOpNode,
    BinOpNode,
    NumNode,
    IdNode,
    BoolNode,
    IfNode,
    BlockNode,
    WhileNode,
    ForNode,
)
from tokens import Token, TokenType

class Interpreter:
    def __init__(self):
        self.env = {}

    def interpret(self, node):
        if isinstance(node, ProgramNode):
            result = None
            for statement in node.statements:
                result = self.interpret(statement)
            return result

        if isinstance(node, BlockNode):
            result = None
            for statement in node.statements:
                result = self.interpret(statement)
            return result

        if isinstance(node, IfNode):
            result = None
            cond = None
            if isinstance(node.cond, BoolNode):
                cond = node.cond.val
            else:
                cond = self.interpret(node.cond)
            if cond:
                result = self.interpret(node.a)
            else: result = self.interpret(node.b)
            if node.c: result = self.interpret(node.c)

            return result

        if isinstance(node, WhileNode):
            result = None
            cond = None
            reCheck = False

            cond = self.interpret(node.cond)
            reCheck = True

            while cond: 
                result = self.interpret(node.a)
                if reCheck: cond = self.interpret(node.cond)
            if node.c: result = self.interpret(node.c)

            return result

        if isinstance(node, ForNode):
            result = None
            for assignment in node.assignments:
                self.interpret(assignment)

            cond = self.interpret(node.cond)
            while cond:
                result = self.interpret(node.a)
                self.interpret(node.block)
                cond = self.interpret(node.cond)
            if node.c: result = self.interpret(node.c)

            return result


        if isinstance(node, AssignNode):
            val = self.interpret(node.expr)
            self.env[node.name.val] = val
            return val

        if isinstance(node, PrintNode):
            val = self.interpret(node.expr)
            print(val)
            return val

        if isinstance(node, CompOpNode):
            a = self.interpret(node.a)
            b = self.interpret(node.b)

            match node.op.type:
                case TokenType.EQ:
                    return a == b
                case TokenType.NEQ:
                    return a != b
                case TokenType.LESS:
                    return a < b
                case TokenType.LEQ:
                    return a <= b
                case TokenType.GREATER:
                    return a > b
                case TokenType.GEQ:
                    return a >= b


        if isinstance(node, BoolOpNode):
            a = self.interpret(node.a)
            b = self.interpret(node.b)

            match node.op.type:
                case TokenType.AND:
                    return a and b
                case TokenType.OR:
                    return a or b
                case _:
                    raise RuntimeError(f"Unknown operator: {node.op}")

        if isinstance(node, BinOpNode):
            a = self.interpret(node.a)
            b = self.interpret(node.b)

            match node.op.type:
                case TokenType.PLUS:
                    return a + b
                case TokenType.MINUS:
                    return a - b
                case TokenType.STAR:
                    return a * b
                case TokenType.SLASH:
                    if b == 0:
                        raise ZeroDivisionError("Runtime Error: Division by zero")
                    return a // b 
                case _:
                    raise RuntimeError(f"Unknown operator: {node.op}")

        if isinstance(node, NumNode):
            return node.val
        
        if isinstance(node, IdNode):
            if node.name not in self.env:
                raise RuntimeError(f"Runtime Error: Undefined variable '{node.name}'")
            return self.env[node.name]

        if isinstance(node, BoolNode):
            if node.val == "true":
                return True
            else:
                return False

        raise RuntimeError(f"Unknown AST Node: {type(node).__name__}")
