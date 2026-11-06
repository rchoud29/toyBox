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
    IfNode,
    WhileNode,
    ForNode,
    StrNode,
)
from tokens import TokenType, Token

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.step = False

    def syntax_error(self, msg, token=None):
        token = token or self.peek()
        
        # Safely extract line, column, or position info from token or lexer
        line = getattr(token, 'line', getattr(self.lexer, 'line', None))
        col = getattr(token, 'col', getattr(token, 'column', getattr(self.lexer, 'col', getattr(self.lexer, 'column', None))))
        pos = getattr(token, 'pos', getattr(self.lexer, 'pos', None))

        location_parts = []
        if line is not None:
            location_parts.append(f"line {line}")
        if col is not None:
            location_parts.append(f"column {col}")
        elif pos is not None:
            location_parts.append(f"pos {pos}")

        loc_str = f"[{', '.join(location_parts)}] " if location_parts else ""
        
        token_val = getattr(token, 'val', None)
        token_type = getattr(token, 'type', None)
        
        if token_type == TokenType.EOF:
            got_str = "EOF"
        elif token_val is not None:
            got_str = f"'{token_val}'"
        else:
            got_str = repr(token)

        raise SyntaxError(f"{loc_str}{msg}, got {got_str}")

    def raise_error(self, msg):
        self.syntax_error(msg)

    def peek(self):
        self.lexer.return_token(token := self.lexer.next_token())
        return token

    def consume(self, type=None) -> Token:
        token = self.lexer.next_token()
        if token.type != type:
            self.lexer.return_token(token)
            type_name = getattr(type, 'name', str(type))
            self.syntax_error(f"Expected token type '{type_name}'", token)
        
        return token

    def parse_primary(self):
        token = self.peek()

        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER)
            return NumNode(token.val)

        if token.type == TokenType.STRING:
            self.consume(TokenType.STRING)
            return StrNode(token.val)

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

        self.syntax_error("Expected number, identifier, boolean, or '('", token)

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

    def parse_for_statement(self):
        self.consume(TokenType.FOR)
        self.consume(TokenType.LPAREN)
        assignments = []
        assignments.append(self.parse_assignment())
        while self.peek().type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            assignments.append(self.parse_assignment())
        self.consume(TokenType.SEMICOLON)
        cond = self.parse_expression()
        self.consume(TokenType.SEMICOLON)
        block = self.parse_block()
        self.consume(TokenType.RPAREN)
        a = self.parse_block()
        c = None
        if self.peek().type == TokenType.FINALLY:
            self.consume(TokenType.FINALLY)
            c = self.parse_block()

        return ForNode(assignments, cond, block, a, c)

    def parse_while_statement(self):
        self.consume(TokenType.WHILE)
        expr = self.parse_expression()
        a = self.parse_block()
        c = None
        token = self.peek()
        if token.type == TokenType.FINALLY:
            self.consume(TokenType.FINALLY)
            c = self.parse_block()
        return WhileNode(expr, a, c)

    def parse_if_statement(self):
        self.consume(TokenType.IF)
        expr = self.parse_expression()
        a = self.parse_block()
        b = None
        c = None
        token = self.peek()
        if token.type == TokenType.ELSE:
            self.consume(TokenType.ELSE)
            if self.peek().type == TokenType.IF:
                b = self.parse_if_statement()
            else: b = self.parse_block()
            token = self.peek()
        if token.type == TokenType.FINALLY:
            self.consume(TokenType.FINALLY)
            c = self.parse_block()

        return IfNode(expr, a, b, c)

    def parse_statement(self):
        token = self.peek()
        checkDelimiter = False
        if token.type is TokenType.EOF:
            self.syntax_error("Expected statement", token)
        
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
        elif token.type == TokenType.WHILE:
            statement = self.parse_while_statement()
        elif token.type == TokenType.FOR:
            statement = self.parse_for_statement()
        elif token.type == TokenType.LBRACE:
            statement = self.parse_block()
        else:
            self.syntax_error("Unexpected statement start", token)

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
