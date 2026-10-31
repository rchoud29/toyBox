from ASTNode import (
    ProgramNode,
    AssignNode,
    PrintNode,
    BinOpNode,
    NumNode,
    IdNode,
)

"""
    <program>         ::= <statement> [ <statement> ... ]
    <statement>       ::= ( <print_statement> | <assignment> ) ";"
    <print_statement> ::= "print" "(" <expression> ")"
    <assignment>      ::= <identifier> "=" <expression>
    <expression>      ::= <value> [ <operator> <expression> ]
    <operator>        ::= "+" | "-" | "*" | "/"
    <value>           ::= <number> | <identifier>
"""
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

    def raise_error(self, msg):
        self.lexer.raise_error(msg)

    def peek(self):
        self.lexer.return_token(token := self.lexer.next_token())
        return token

    def consume(self, type=None, val=None):
        token = self.lexer.next_token()
        if token is None:
            raise SyntaxError(
                f"Unexpected EOF. Expected type='{type}', value='{val}'")
        
        if type and token[0] != type:
            self.lexer.return_token(token)
            raise SyntaxError(
                f"Position {self.lexer.pos}: Expected token type '{type}', got '{token[0]}' ({token[1]!r})"
            )
        if val and token[1] != val:
            self.lexer.return_token(token)
            raise SyntaxError(
                f"Position {self.lexer.pos}: Expected token value '{val}', got '{token[1]!r}'"
            )

        return token

    def parse_value(self):
        token = self.peek()
        if token is None:
            raise SyntaxError("Expected value, got EOF")

        type, val = token

        match type:
            case "number":
                self.consume("number")
                return NumNode(val)
            case "identifier":
                self.consume("identifier")
                return IdNode(val)
            case _:
                raise SyntaxError(f"Expected legal type, got '{type}'")

    def parse_expression(self):
        left = self.parse_value()
        token = self.peek()
        if token and token[0] == "operator":
            _, op = self.consume("operator")
            right = self.parse_expression()
            return BinOpNode(op, left, right)
        return left

    def parse_print_statement(self):
        self.consume("identifier", "print")
        self.consume("punctuation", '(')
        expr = self.parse_expression()
        self.consume("punctuation", ')')
        return PrintNode(expr)

    def parse_assignment(self):
        _, id = self.consume("identifier")
        self.consume("punctuation", '=')
        expr = self.parse_expression()
        return AssignNode(id, expr)

    def parse_statement(self):
        token = self.peek()
        if token is None:
            raise SyntaxError("Expected statement, got EOF")
        
        if token[0] == "identifier" and token[1] == "print":
            statement = self.parse_print_statement()
        elif token[0] == "identifier":
            statement = self.parse_assignment()
        else:
            raise SyntaxError("Unexpected token: '{token[1]}'")

        self.consume("punctuation", ';')
        return statement


    def parse_program(self):
        statements = []
        while self.peek() is not None:
            statements.append(self.parse_statement())

        return ProgramNode(statements)
