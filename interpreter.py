from ASTNode import (
    ProgramNode,
    AssignNode,
    PrintNode,
    BinOpNode,
    NumNode,
    IdNode
)

class Interpreter:
    def __init__(self):
        self.env = {}

    def interpret(self, node):
        if isinstance(node, ProgramNode):
            result = None
            for statement in node.statements:
                result = self.interpret(statement)
            return result

        if isinstance(node, AssignNode):
            val = self.interpret(node.expr)
            self.env[node.name] = val
            return val

        if isinstance(node, PrintNode):
            val = self.interpret(node.expr)
            print(val)
            return val

        if isinstance(node, BinOpNode):
            a = self.interpret(node.left)
            b = self.interpret(node.right)

            match node.op:
                case '+':
                    return a + b
                case '-':
                    return a - b
                case '*':
                    return a * b
                case '/':
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

        raise RuntimeError(f"Unknown AST Node: {type(node).__name__}")
