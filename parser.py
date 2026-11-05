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
    BlockNode,
    IfNode
)
from tokens import TokenType, Token

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.step = False

    def raise_error(self, msg):
        self.lexer.raise_error(msg)

    def peek(self):
        self.lexer.return_token(token := self.lexer.next_token())
        return token

    def consume(self, type=None) -> Token:
        token = self.lexer.next_token()
        if token.type != type:
            self.lexer.return_token(token)
            raise SyntaxError(f"({self.lexer.pos}) Expected {type.name}, got {token!r}")
        
        return token


    def parse_primary(self):
        token = self.peek()

        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER)
            return NumNode(token.val)

        if token.type == TokenType.IDENTIFIER:
            self.consume(TokenType.IDENTIFIER)
            return IdNode(token.val)

        if token.type == TokenType.BOOLEAN:
            self.consume(TokenType.BOOLEAN)
            return BoolNode(token.val)

        if token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"({self.lexer.pos}) Expected val or '(', got {token!r}")

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
            return CompOpNode(op, a, b)
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
        if self.step: input(f"{self.peek()}> ")
        self.consume(TokenType.ASSIGN)
        expr = self.parse_expression()
        return AssignNode(id, expr)


    def parse_if_statement(self):
        self.consume(TokenType.IF)
        expr = self.parse_expression()
        a = self.parse_block()
        b = None
        token = self.peek()
        if token.type == TokenType.ELSE:
            self.consume(TokenType.ELSE)
            b = self.parse_block()

        return IfNode(expr, a, b)

    def parse_statement(self):
        #<statement>			::= ( <print_statement> | <assignment> ) ";"
        token = self.peek()
        checkDelimiter = False
        if token.type is TokenType.EOF:
            raise SyntaxError("Expected statement, got EOF")
        
        if self.step: 
            input(f"{token}>")
        if token.type == TokenType.PRINT:
            statement = self.parse_print_statement()
            checkDelimiter = True
        elif token.type == TokenType.IDENTIFIER:
            statement = self.parse_assignment()
            checkDelimiter = True
        elif token.type == TokenType.IF:
            statement = self.parse_if_statement()
        else:
            raise SyntaxError(f"Unexpected token: '{token.val}'")

        if checkDelimiter: self.consume(TokenType.SEMICOLON)
        if self.step: print(statement)
        return statement

    def parse_block(self):
        self.consume(TokenType.LBRACE)
        statements = []
        while self.peek().type != TokenType.EOF and \
              self.peek().type != TokenType.RBRACE:
            statements.append(self.parse_statement())
        self.consume(TokenType.RBRACE)
        return BlockNode(statements)

    def parse_program(self):
        #<program>			::= <statement> [ <statement> ... ]
        statements = []
        while self.peek().type != TokenType.EOF:
            statements.append(self.parse_statement())

        return ProgramNode(statements)

    def step_program(self):
        self.step = True
        statements = []

        while self.peek().type != TokenType.EOF:
            statements.append(self.parse_statement())

        return ProgramNode(statements)
