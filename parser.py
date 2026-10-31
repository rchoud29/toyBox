from ASTNode import (
    ProgramNode,
    AssignNode,
    PrintNode,
    BinOpNode,
    NumNode,
    IdNode,
)
from tokens import TokenType, Token

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

    def raise_error(self, msg):
        self.lexer.raise_error(msg)

    def peek(self):
        self.lexer.return_token(token := self.lexer.next_token())
        return token

    def consume(self, type=None) -> Token:
        token = self.lexer.next_token()
        if token.type != type:
            self.lexer.return_token(token)
            raise SyntaxError(f"Expected {type.name}, got {token!r}")
        
        return token


    def parse_primary(self):
        token = self.peek()

        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER)
            return NumNode(token.val)

        if token.type == TokenType.IDENTIFIER:
            self.consume(TokenType.IDENTIFIER)
            return IdNode(token.val)

        if token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"Expected val or '(', got {token!r}")

    def parse_factor(self):
        a = self.parse_primary()

        multTypes = (
            TokenType.STAR,
            TokenType.SLASH,
        )

        token = self.peek()
        if token.type in multTypes:
            op = self.lexer.next_token()
            b = self.parse_term()
            return BinOpNode(op, a, b)
        return a


    def parse_term(self):
        a = self.parse_factor()

        addTypes = (
            TokenType.PLUS,
            TokenType.MINUS,
        )

        token = self.peek()
        if token.type in addTypes:
            op = self.lexer.next_token()
            b = self.parse_term()
            return BinOpNode(op, a, b)
        return a


    def parse_comparison(self):
        a = self.parse_term()

        compTypes = (
            TokenType.EQ,
            TokenType.NEQ,
            TokenType.LESS,
            TokenType.LEQ,
            TokenType.GREATER,
            TokenType.GEQ,
        )

        token = self.peek()
        if token.type in compTypes:
            op = self.lexer.next_token()
            b = self.parse_comparison()
            return BoolOpNode(op, a, b)
        return a

    def parse_logic_and(self):
        a = self.parse_comparison()
        
        token = self.peek()
        if token.type == TokenType.AND:
            op = self.lexer.next_token()
            b = self.parse_logic_and()
            return BoolOpNode(op, a, b)
        return a

    def parse_expression(self):
        a = self.parse_logic_and()

        token = self.peek()
        if token.type == TokenType.OR:
            op = self.lexer.next_token()
            b = self.parse_expression()
            return BoolOpNode(op, a, b)
        return a

    def parse_print_statement(self):
        self.consume(TokenType.PRINT)
        self.consume(TokenType.LPAREN)
        expr = self.parse_expression()
        self.consume(TokenType.RPAREN)
        return PrintNode(expr)

    def parse_assignment(self):
        id = self.consume(TokenType.IDENTIFIER)
        self.consume(TokenType.ASSIGN)
        expr = self.parse_expression()
        return AssignNode(id.val, expr)

    def parse_statement(self):
        #<statement>			::= ( <print_statement> | <assignment> ) ";"
        token = self.peek()
        if token.type is TokenType.EOF:
            raise SyntaxError("Expected statement, got EOF")

        if token.type == TokenType.PRINT:
            statement = self.parse_print_statement()
        elif token.type == TokenType.IDENTIFIER:
            statement = self.parse_assignment()
        else:
            raise SyntaxError("Unexpected token: '{token.val}'")

        self.consume(TokenType.SEMICOLON)
        return statement


    def parse_program(self):
        #<program>			::= <statement> [ <statement> ... ]
        statements = []
        while self.peek().type != TokenType.EOF:
            statements.append(self.parse_statement())

        return ProgramNode(statements)
