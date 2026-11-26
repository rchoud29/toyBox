from tokens import TokenKind as K
from ast_nodes import *

COMPOUND_OPS = {
    K.PLUS_ASSIGN: K.PLUS,
    K.MINUS_ASSIGN: K.MINUS,
    K.STAR_ASSIGN: K.STAR,
    K.SLASH_ASSIGN: K.SLASH,
    K.PERCENT_ASSIGN: K.PERCENT,
}

UPDATE_OPS = {
    K.INCREMENT: K.PLUS,
    K.DECREMENT: K.MINUS,
}


class ParserError(Exception):
    pass


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def at_end(self):
        return self.check(K.EOF)

    def advance(self):
        t = self.peek()
        if not self.at_end():
            self.pos += 1
        return t

    def check(self, k):
        return self.peek().kind == k

    def match(self, *kinds):
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def error(self, msg):
        t = self.peek()
        return ParserError(f'{t.line}:{t.column}: {msg}; found {t.lexeme!r}')

    def expect(self, k):
        if not self.check(k):
            raise self.error(f'Expected {k.name}')
        return self.advance()

    def parse_program(self):
        fs = []
        while not self.at_end():
            fs.append(self.parse_function())
        return Program(fs)

    def parse_function(self):
        self.expect(K.FN)
        name = self.expect(K.IDENTIFIER).lexeme
        self.expect(K.LPAREN)
        ps = [] if self.check(K.RPAREN) else self.parse_parameters()
        self.expect(K.RPAREN)
        self.expect(K.COLON)
        return Function(name, ps, self.parse_type(), self.parse_block())

    def parse_parameters(self):
        ps = [self.parse_parameter()]
        while self.match(K.COMMA):
            ps.append(self.parse_parameter())
        return ps

    def parse_parameter(self):
        name = self.expect(K.IDENTIFIER).lexeme
        self.expect(K.COLON)
        return Parameter(name, self.parse_type())

    def parse_block(self):
        self.expect(K.LBRACE)
        ss = []
        while not self.check(K.RBRACE):
            ss.append(self.parse_statement())
        self.expect(K.RBRACE)
        return Block(ss)

    def parse_statement(self):
        methods = {K.DF: self.parse_declaration,
            K.ST: self.parse_assignment,
            K.RETURN: self.parse_return_stmt,
            K.IF: self.parse_if_stmt,
            K.WHILE: self.parse_while_stmt,
            K.FOR: self.parse_for_stmt}
        if self.peek().kind in methods:
            return methods[self.peek().kind]()
        if self.check(K.IDENTIFIER):
            c = self.parse_call()
            self.expect(K.SEMICOLON)
            return CallStatement(c)
        raise self.error('Expected statement')

    def parse_declaration(self, semi=True):
        self.expect(K.DF)
        bs = [self.parse_binding()]
        while self.match(K.COMMA):
            bs.append(self.parse_binding())
        if semi:
            self.expect(K.SEMICOLON)
        return Declaration(bs)

    def parse_binding(self):
        name = self.expect(K.IDENTIFIER).lexeme
        self.expect(K.COLON)
        t = self.parse_type()
        value = None
        if self.match(K.ASSIGN):
            value = self.parse_expression()
        return Binding(name, t, value)

    def parse_assignment(self, semi=True):
        self.expect(K.ST)
        name = self.expect(K.IDENTIFIER).lexeme
        op = self.peek().kind

        if op in UPDATE_OPS:
            self.advance()
            value = BinaryExpression(
                Identifier(name), UPDATE_OPS[op], Integer(1)
            )
        else:
            if op != K.ASSIGN and op not in COMPOUND_OPS:
                raise self.error('Expected assignment operator')
            self.advance()
            value = self.parse_expression()
            if op in COMPOUND_OPS:
                value = BinaryExpression(
                    Identifier(name), COMPOUND_OPS[op], value
                )

        if semi:
            self.expect(K.SEMICOLON)
        return Assignment(name, value)

    def parse_return_stmt(self):
        self.expect(K.RETURN)
        v = None if self.check(K.SEMICOLON) else self.parse_expression()
        self.expect(K.SEMICOLON)
        return Return(v)

    def parse_if_stmt(self):
        self.expect(K.IF)
        self.expect(K.LPAREN)
        c = self.parse_expression()
        self.expect(K.RPAREN)
        b = self.parse_block()
        e = None
        if self.match(K.ELSE):
            e = (
                self.parse_if_stmt() if self.check(K.IF)
                else self.parse_block()
            )
        return If(c, b, e)

    def parse_while_stmt(self):
        self.expect(K.WHILE)
        self.expect(K.LPAREN)
        c = self.parse_expression()
        self.expect(K.RPAREN)
        return While(c, self.parse_block())

    def parse_for_stmt(self):
        self.expect(K.FOR)
        self.expect(K.LPAREN)

        init = None
        if self.check(K.DF):
            init = self.parse_declaration(False)
        elif not self.check(K.SEMICOLON):
            init = self.parse_assignment(False)
        self.expect(K.SEMICOLON)

        cond = Boolean(True)
        if not self.check(K.SEMICOLON):
            cond = self.parse_expression()
        self.expect(K.SEMICOLON)

        update = None
        if not self.check(K.RPAREN):
            update = self.parse_assignment(False)
        self.expect(K.RPAREN)

        return For(init, cond, update, self.parse_block())

    def parse_expression(self):
        return self.parse_equality()

    def binary(self, lower, kinds):
        left = lower()
        while self.peek().kind in kinds:
            left = BinaryExpression(left, self.advance().kind, lower())
        return left

    def parse_equality(self):
        return self.binary(self.parse_comparison, (K.EQ, K.NEQ))

    def parse_comparison(self):
        return self.binary(self.parse_additive, (K.LT, K.GT, K.LTE, K.GTE))

    def parse_additive(self):
        return self.binary(self.parse_multiplicative, (K.PLUS, K.MINUS))

    def parse_multiplicative(self):
        return self.binary(self.parse_unary, (K.STAR, K.SLASH, K.PERCENT))

    def parse_unary(self):
        if self.peek().kind in (K.MINUS, K.NOT):
            return UnaryExpression(self.advance().kind, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        v = self.parse_primary()
        while self.match(K.COLON):
            v = Cast(self.parse_type(), v)
        return v

    def parse_primary(self):
        if self.check(K.INTEGER):
            return Integer(int(self.advance().lexeme))
        if self.match(K.TRUE):
            return Boolean(True)
        if self.match(K.FALSE):
            return Boolean(False)
        if self.check(K.IDENTIFIER):
            if self.peek(1).kind == K.LPAREN:
                return self.parse_call()
            return Identifier(self.advance().lexeme)
        if self.match(K.LPAREN):
            v = self.parse_expression()
            self.expect(K.RPAREN)
            return v
        raise self.error('Expected expression')

    def parse_call(self):
        name = self.expect(K.IDENTIFIER).lexeme
        self.expect(K.LPAREN)
        args = [] if self.check(K.RPAREN) else self.parse_arguments()
        self.expect(K.RPAREN)
        return Call(name, args)

    def parse_arguments(self):
        args = [self.parse_expression()]
        while self.match(K.COMMA):
            args.append(self.parse_expression())
        return args

    def parse_type(self):
        return Type(self.expect(K.IDENTIFIER).lexeme)
