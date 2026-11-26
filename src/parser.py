from tokens import Token, TokenKind
from ast_nodes import *


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # Cursor management
    def peek(self, offset: int = 0) -> Token:
        index = self.pos + offset

        if index < 0 or index >= len(self.tokens):
            raise ParserError("Token index out of bounds")

        return self.tokens[index]

    def at_end(self) -> bool:
        return self.peek().kind == TokenKind.EOF

    def advance(self) -> Token:
        token = self.peek()

        if not self.at_end():
            self.pos += 1

        return token

    def check(self, kind: TokenKind) -> bool:
        return self.peek().kind == kind

    def match(self, *kinds: TokenKind) -> bool:
        if self.peek().kind in kinds:
            self.advance()
            return True

        return False

    def expect(self, kind: TokenKind) -> Token:
        if self.check(kind):
            return self.advance()

        raise ParserError(
            f"Expected {kind.name}, "
            f"got {self.peek().kind.name}",
            self.peek()
        )

    # Program structure

    # program = { function }, EOF ;

    def parse_program(self) -> Program:
        functions = []

        while not self.at_end():
            functions.append(self.parse_function())

        self.expect(TokenKind.EOF)

        return Program(functions)

    # function = "fn", id, "(", [ parameters ], ")",
    #            ":", type, block ;

    def parse_function(self) -> Function:
        self.expect(TokenKind.FN)

        name = self.expect(TokenKind.IDENTIFIER).lexeme

        self.expect(TokenKind.LPAREN)

        parameters = []

        if not self.check(TokenKind.RPAREN):
            parameters = self.parse_parameters()

        self.expect(TokenKind.RPAREN)
        self.expect(TokenKind.COLON)

        return_type = self.parse_type()
        body = self.parse_block()

        return Function(name, parameters, return_type, body)

    # parameters = parameter, { ",", parameter } ;

    def parse_parameters(self) -> list[Parameter]:
        parameters = [self.parse_parameter()]

        while self.match(TokenKind.COMMA):
            parameters.append(self.parse_parameter())

        return parameters

    # parameter = id, ":", type ;

    def parse_parameter(self) -> Parameter:
        name = self.expect(TokenKind.IDENTIFIER).lexeme

        self.expect(TokenKind.COLON)

        data_type = self.parse_type()

        return Parameter(name, data_type)

    # block = "{", { statement }, "}" ;

    def parse_block(self) -> Block:
        self.expect(TokenKind.LBRACE)

        statements = []

        while not self.check(TokenKind.RBRACE):
            if self.at_end():
                raise ParserError(
                    "Expected '}' before EOF",
                    self.peek()
                )

            statements.append(self.parse_statement())

        self.expect(TokenKind.RBRACE)

        return Block(statements)

    # Statements

    # statement = declaration
    #           | assignment
    #           | return_stmt
    #           | if_stmt
    #           | while_stmt
    #           | call, ";" ;

    def parse_statement(self) -> Statement:
        kind = self.peek().kind

        if kind == TokenKind.DF:
            return self.parse_declaration()

        if kind == TokenKind.ST:
            return self.parse_assignment()

        if kind == TokenKind.RETURN:
            return self.parse_return_stmt()

        if kind == TokenKind.IF:
            return self.parse_if_stmt()

        if kind == TokenKind.WHILE:
            return self.parse_while_stmt()

        if kind == TokenKind.IDENTIFIER:
            call = self.parse_call()
            self.expect(TokenKind.SEMICOLON)

            return CallStatement(call)

        raise ParserError(
            "Expected statement",
            self.peek()
        )

    # declaration = "df", id, ":", type,
    #               "=", expression, ";" ;

    def parse_declaration(self) -> Declaration:
        self.expect(TokenKind.DF)

        name = self.expect(TokenKind.IDENTIFIER).lexeme

        self.expect(TokenKind.COLON)

        data_type = self.parse_type()

        self.expect(TokenKind.ASSIGN)

        value = self.parse_expression()

        self.expect(TokenKind.SEMICOLON)

        return Declaration(name, data_type, value)

    # assignment = "st", id, "=", expression, ";" ;

    def parse_assignment(self) -> Assignment:
        self.expect(TokenKind.ST)

        name = self.expect(TokenKind.IDENTIFIER).lexeme

        self.expect(TokenKind.ASSIGN)

        value = self.parse_expression()

        self.expect(TokenKind.SEMICOLON)

        return Assignment(name, value)

    # return_stmt = "return", [ expression ], ";" ;

    def parse_return_stmt(self) -> Return:
        self.expect(TokenKind.RETURN)

        value = None

        if not self.check(TokenKind.SEMICOLON):
            value = self.parse_expression()

        self.expect(TokenKind.SEMICOLON)

        return Return(value)

    # if_stmt = "if", "(", expression, ")", block,
    #           [ "else", ( block | if_stmt ) ] ;

    def parse_if_stmt(self) -> If:
        self.expect(TokenKind.IF)
        self.expect(TokenKind.LPAREN)

        condition = self.parse_expression()

        self.expect(TokenKind.RPAREN)

        body = self.parse_block()
        else_body = None

        if self.match(TokenKind.ELSE):
            if self.check(TokenKind.IF):
                else_body = self.parse_if_stmt()
            else:
                else_body = self.parse_block()

        return If(condition, body, else_body)

    # while_stmt = "while", "(", expression, ")", block ;

    def parse_while_stmt(self) -> While:
        self.expect(TokenKind.WHILE)
        self.expect(TokenKind.LPAREN)

        condition = self.parse_expression()

        self.expect(TokenKind.RPAREN)

        body = self.parse_block()

        return While(condition, body)

    # Expressions

    # expression = equality ;

    def parse_expression(self) -> Expression:
        return self.parse_equality()

    # equality = comparison,
    #            { ( "==" | "!=" ), comparison } ;

    def parse_equality(self) -> Expression:
        left = self.parse_comparison()

        while self.peek().kind in (
            TokenKind.EQ,
            TokenKind.NEQ
        ):
            op = self.advance().kind
            right = self.parse_comparison()

            left = BinaryExpression(left, op, right)

        return left

    # comparison = additive,
    #              { ( "<" | ">" | "<=" | ">=" ), additive } ;

    def parse_comparison(self) -> Expression:
        left = self.parse_additive()

        while self.peek().kind in (
            TokenKind.LT,
            TokenKind.GT,
            TokenKind.LTE,
            TokenKind.GTE
        ):
            op = self.advance().kind
            right = self.parse_additive()

            left = BinaryExpression(left, op, right)

        return left

    # additive = multiplicative,
    #            { ( "+" | "-" ), multiplicative } ;

    def parse_additive(self) -> Expression:
        left = self.parse_multiplicative()

        while self.peek().kind in (
            TokenKind.PLUS,
            TokenKind.MINUS
        ):
            op = self.advance().kind
            right = self.parse_multiplicative()

            left = BinaryExpression(left, op, right)

        return left

    # multiplicative = unary,
    #                  { ( "*" | "/" | "%" ), unary } ;

    def parse_multiplicative(self) -> Expression:
        left = self.parse_unary()

        while self.peek().kind in (
            TokenKind.STAR,
            TokenKind.SLASH,
            TokenKind.PERCENT
        ):
            op = self.advance().kind
            right = self.parse_unary()

            left = BinaryExpression(left, op, right)

        return left

    # unary = ( "-" | "!" ), unary
    #       | postfix ;

    def parse_unary(self) -> Expression:
        if self.peek().kind in (
            TokenKind.MINUS,
            TokenKind.NOT
            ):
            op = self.advance().kind
            operand = self.parse_unary()

            return UnaryExpression(op, operand)

        return self.parse_postfix()

    # postfix = primary, { ":", type } ;

    def parse_postfix(self) -> Expression:
        value = self.parse_primary()

        while self.match(TokenKind.COLON):
            data_type = self.parse_type()
            value = Cast(data_type, value)

        return value

    # primary = int
    #         | bool
    #         | id, [ "(", [ arguments ], ")" ]
    #         | "(", expression, ")" ;

    def parse_primary(self) -> Expression:
        kind = self.peek().kind

        if kind == TokenKind.INTEGER:
            token = self.advance()

            return Integer(int(token.lexeme))

        if kind == TokenKind.TRUE:
            self.advance()

            return Boolean(True)

        if kind == TokenKind.FALSE:
            self.advance()

            return Boolean(False)

        if kind == TokenKind.IDENTIFIER:
            if self.peek(1).kind == TokenKind.LPAREN:
                return self.parse_call()

            return Identifier(self.advance().lexeme)

        if self.match(TokenKind.LPAREN):
            expression = self.parse_expression()

            self.expect(TokenKind.RPAREN)

            return expression

        raise ParserError(
            "Expected expression",
            self.peek()
        )

    # Function calls

    # call = id, "(", [ arguments ], ")" ;

    def parse_call(self) -> Call:
        name = self.expect(TokenKind.IDENTIFIER).lexeme

        self.expect(TokenKind.LPAREN)

        arguments = []

        if not self.check(TokenKind.RPAREN):
            arguments = self.parse_arguments()

        self.expect(TokenKind.RPAREN)

        return Call(name, arguments)

    # arguments = expression, { ",", expression } ;

    def parse_arguments(self) -> list[Expression]:
        arguments = [self.parse_expression()]

        while self.match(TokenKind.COMMA):
            arguments.append(self.parse_expression())

        return arguments

    # Types

    # type = id ;

    def parse_type(self) -> Type:
        name = self.expect(TokenKind.IDENTIFIER).lexeme

        return Type(name)


class ParserError(Exception):
    def __init__(
        self,
        message: str,
        token: Token | None = None
    ):
        if token is None:
            super().__init__(f"ParserError: {message}")
            return

        super().__init__(
            f"ParserError at {token.line}:{token.column}: "
            f"{message}\n"
            f"Found: {token.lexeme!r}"
        )
