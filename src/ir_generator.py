import ast_nodes as a
from ir import *
from typesys import VOID, INT_LITERAL
from tokens import TokenKind as K
BINARY_OPS = {K.PLUS: Opcode.ADD,
    K.MINUS: Opcode.SUB,
    K.STAR: Opcode.MUL,
    K.SLASH: Opcode.DIV,
    K.PERCENT: Opcode.MOD,
    K.EQ: Opcode.EQ,
    K.NEQ: Opcode.NEQ,
    K.LT: Opcode.LT,
    K.GT: Opcode.GT,
    K.LTE: Opcode.LTE,
    K.GTE: Opcode.GTE}


class IRGenerator:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def generate(self, program):
        self.module = IRModule()
        for f in program.functions:
            self.generate_function(f)
        return self.module

    def symbol(self, n):
        return self.analyzer.resolved_symbols[id(n)]

    def emit(self, op, args=(), result=None):
        self.block.append(Instruction(op, list(args), result))

    def value(self, op, t, args):
        v = Temporary(self.temp_count, t)
        self.temp_count += 1
        self.emit(op, args, v)
        return v

    def allocate(self, s):
        v = Address(len(self.addresses), s.type)
        self.addresses[id(s)] = v
        ins = self.function.blocks[0].instructions
        i = 0
        while i < len(ins) and ins[i].opcode == Opcode.ALLOC:
            i += 1
        ins.insert(i, Instruction(Opcode.ALLOC, result=v))
        return v

    def label(self, p):
        l = Label(f'{p}.{self.label_count}')
        self.label_count += 1
        return l

    def start(self, l):
        self.block = BasicBlock(l)
        self.function.append(self.block)

    def terminated(self):
        return self.block is None or self.block.terminated

    def generate_function(self, n):
        s = self.symbol(n)
        self.temp_count = 0
        self.label_count = 0
        self.addresses = {}
        ps = [IRParameter(p.name.lower(), p.type) for p in s.parameters]
        self.function = IRFunction(s.name.lower(), ps, s.return_type)
        self.module.append(self.function)
        self.start(Label('entry'))
        for p, sym in zip(ps, s.parameters):
            self.emit(Opcode.STORE, [p, self.allocate(sym)])
        self.generate_block(n.body)
        if not self.terminated():
            if s.return_type != VOID:
                raise IRError('Missing return')
            self.emit(Opcode.RET)

    def generate_block(self, n):
        for s in n.statements:
            if self.terminated():
                break
            self.generate_statement(s)

    def generate_statement(self, n):
        if isinstance(n, a.Declaration):
            for b in n.bindings:
                addr = self.allocate(self.symbol(b))
                if b.value is not None:
                    v = self.generate_expression(b.value)
                    self.emit(Opcode.STORE, [v, addr])
        elif isinstance(n, a.Assignment):
            self.emit(Opcode.STORE,
                [self.generate_expression(n.value),
                self.addresses[id(self.symbol(n))]])
        elif isinstance(n, a.Return):
            self.emit(Opcode.RET,
                [] if n.value is None else [self.generate_expression(n.value)])
        elif isinstance(n, a.CallStatement):
            self.generate_call(n.call)
        elif isinstance(n, a.If):
            self.generate_if(n)
        elif isinstance(n, a.While):
            self.generate_while(n)
        elif isinstance(n, a.For):
            self.generate_for(n)
        else:
            raise IRError('Unknown statement')

    def generate_if(self, n):
        c = self.generate_expression(n.condition)
        yes = self.label('if.true')
        end = self.label('if.end')
        no = self.label('if.false') if n.else_body else end
        self.emit(Opcode.BR, [c, yes, no])
        self.start(yes)
        self.generate_block(n.body)
        y = not self.terminated()
        if y:
            self.emit(Opcode.JMP, [end])
        z = n.else_body is None
        if n.else_body:
            self.start(no)
            if isinstance(n.else_body, a.Block):
                self.generate_block(n.else_body)
            else:
                self.generate_if(n.else_body)
            z = not self.terminated()
            if z:
                self.emit(Opcode.JMP, [end])
        if y or z:
            self.start(end)
        else:
            self.block = None

    def generate_while(self, n):
        c = self.label('while.cond')
        b = self.label('while.body')
        e = self.label('while.end')
        self.emit(Opcode.JMP, [c])
        self.start(c)
        self.emit(Opcode.BR, [self.generate_expression(n.condition), b, e])
        self.start(b)
        self.generate_block(n.body)
        if not self.terminated():
            self.emit(Opcode.JMP, [c])
        self.start(e)

    def generate_for(self, n):
        if n.init is not None:
            self.generate_statement(n.init)

        cond = self.label('for.cond')
        body = self.label('for.body')
        end = self.label('for.end')

        self.emit(Opcode.JMP, [cond])
        self.start(cond)
        test = self.generate_expression(n.condition)
        self.emit(Opcode.BR, [test, body, end])

        self.start(body)
        self.generate_block(n.body)
        if not self.terminated():
            if n.update is not None:
                self.generate_statement(n.update)
            self.emit(Opcode.JMP, [cond])

        self.start(end)

    def generate_expression(self, n):
        t = self.analyzer.expression_types[id(n)]
        cv = self.analyzer.constant_values
        if id(n) in cv:
            if t == INT_LITERAL:
                raise IRError('Unresolved literal')
            return Constant(cv[id(n)], t)
        if isinstance(n, a.Identifier):
            return self.value(Opcode.LOAD,
                t,
                [self.addresses[id(self.symbol(n))]])
        if isinstance(n, a.BinaryExpression):
            return self.value(BINARY_OPS[n.op],
                t,
                [self.generate_expression(n.left),
                self.generate_expression(n.right)])
        if isinstance(n, a.UnaryExpression):
            return self.value(Opcode.NEG if n.op == K.MINUS else Opcode.NOT,
                t,
                [self.generate_expression(n.operand)])
        if isinstance(n, a.Cast):
            v = self.generate_expression(n.value)
            return v if v.type == t else self.value(Opcode.CAST, t, [v])
        if isinstance(n, a.Call):
            return self.generate_call(n)
        raise IRError('Unknown expression')

    def generate_call(self, n):
        s = self.symbol(n)
        args = [FunctionRef(s.name.lower())]
        args += [self.generate_expression(v) for v in n.arguments]
        if s.return_type == VOID:
            self.emit(Opcode.CALL, args)
            return None
        return self.value(Opcode.CALL, s.return_type, args)
