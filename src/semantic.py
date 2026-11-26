import ast_nodes as a
from typesys import *
from symbols import *
from tokens import TokenKind as K
class SemanticError(Exception): pass
ARITH=(K.PLUS,K.MINUS,K.STAR,K.SLASH,K.PERCENT)
ORDER=(K.LT,K.GT,K.LTE,K.GTE)
EQ=(K.EQ,K.NEQ)
def divide(x,y):
    if y==0: raise SemanticError('Division by zero')
    return (abs(x)//abs(y))*(-1 if (x<0)!=(y<0) else 1)
class SemanticAnalyzer:
    def __init__(self):
        self.global_scope=Scope(); self.scope=self.global_scope; self.current_function=None
        self.expression_types={}; self.resolved_symbols={}; self.constant_values={}
    def analyze(self,program):
        self.__init__()
        try:
            for f in program.functions: self.register_function(f)
            for f in program.functions: self.analyze_function(f)
        except (TypeError,SymbolError) as e: raise SemanticError(str(e)) from e
        return program
    def register_function(self,f):
        ps=[VariableSymbol(p.name,resolve_type(p.type.name)) for p in f.parameters]
        if any(p.type==VOID for p in ps): raise SemanticError('Void parameter')
        s=FunctionSymbol(f.name,ps,resolve_type(f.return_type.name)); self.scope.define(s); self.resolved_symbols[id(f)]=s
        for p,sym in zip(f.parameters,ps): self.resolved_symbols[id(p)]=sym
    def analyze_function(self,f):
        s=self.resolved_symbols[id(f)]; self.current_function=s; self.scope=Scope(self.global_scope)
        try:
            for p in s.parameters: self.scope.define(p)
            self.analyze_block(f.body,False)
            if s.return_type!=VOID and not self.block_returns(f.body): raise SemanticError(f'{f.name} may not return')
        finally: self.scope=self.global_scope; self.current_function=None
    def analyze_block(self,b,new_scope=True):
        old=self.scope
        if new_scope: self.scope=Scope(old)
        try:
            for s in b.statements: self.analyze_statement(s)
        finally: self.scope=old
    def analyze_statement(self,n):
        if isinstance(n,a.Declaration):
            for b in n.bindings:
                t=resolve_type(b.type.name)
                if t==VOID: raise SemanticError('Void variable')
                self.analyze_expression(b.value,t); s=VariableSymbol(b.name,t); self.scope.define(s); self.resolved_symbols[id(b)]=s
        elif isinstance(n,a.Assignment):
            s=self.scope.resolve(n.name)
            if not isinstance(s,VariableSymbol): raise SemanticError('Expected variable')
            self.analyze_expression(n.value,s.type); self.resolved_symbols[id(n)]=s
        elif isinstance(n,a.Return):
            t=self.current_function.return_type
            if n.value is None:
                if t!=VOID: raise SemanticError('Missing return value')
            else:
                if t==VOID: raise SemanticError('Void function cannot return value')
                self.analyze_expression(n.value,t)
        elif isinstance(n,(a.If,a.While)):
            self.analyze_expression(n.condition,BOOL); self.analyze_block(n.body)
            if isinstance(n,a.If):
                if isinstance(n.else_body,a.Block): self.analyze_block(n.else_body)
                elif n.else_body: self.analyze_statement(n.else_body)
        elif isinstance(n,a.CallStatement): self.analyze_expression(n.call)
        else: raise SemanticError('Unknown statement')
    def block_returns(self,b): return any(self.statement_returns(s) for s in b.statements)
    def statement_returns(self,s):
        if isinstance(s,a.Return): return True
        if isinstance(s,a.If) and s.else_body:
            return self.block_returns(s.body) and (self.block_returns(s.else_body) if isinstance(s.else_body,a.Block) else self.statement_returns(s.else_body))
        return False
    def analyze_expression(self,n,expected=None):
        t=self.infer(n,expected)
        if expected is not None and t!=expected: raise SemanticError(f'Expected {expected}, got {t}')
        self.expression_types[id(n)]=t; return t
    def infer(self,n,expected):
        cv=self.constant_values
        if isinstance(n,a.Integer):
            cv[id(n)]=n.value
            if expected is None or expected==INT_LITERAL: return INT_LITERAL
            if not expected.is_integer() or not expected.fits(n.value): raise SemanticError(f'{n.value} does not fit {expected}')
            return expected
        if isinstance(n,a.Boolean): cv[id(n)]=n.value; return BOOL
        if isinstance(n,a.Identifier):
            s=self.scope.resolve(n.name)
            if not isinstance(s,VariableSymbol): raise SemanticError('Expected variable')
            self.resolved_symbols[id(n)]=s; return s.type
        if isinstance(n,a.Call):
            s=self.scope.resolve(n.name)
            if not isinstance(s,FunctionSymbol) or len(n.arguments)!=len(s.parameters): raise SemanticError(f'Invalid call to {n.name}')
            for v,p in zip(n.arguments,s.parameters): self.analyze_expression(v,p.type)
            self.resolved_symbols[id(n)]=s; return s.return_type
        if isinstance(n,a.Cast):
            src=self.analyze_expression(n.value); t=resolve_type(n.type.name)
            if not can_cast(src,t): raise SemanticError('Invalid cast')
            if id(n.value) in cv: cv[id(n)]=cast_value(cv[id(n.value)],t)
            return t
        if isinstance(n,a.UnaryExpression):
            t=self.analyze_expression(n.operand,BOOL if n.op==K.NOT else None)
            if n.op==K.NOT:
                if id(n.operand) in cv: cv[id(n)]=not cv[id(n.operand)]
                return BOOL
            if t!=INT_LITERAL and not t.is_integer(): raise SemanticError('Expected integer')
            if id(n.operand) in cv:
                v=-cv[id(n.operand)]
                if t==INT_LITERAL and expected is not None and expected!=INT_LITERAL:
                    if not expected.is_integer() or not expected.fits(v): raise SemanticError(f'{v} does not fit {expected}')
                    t=expected
                cv[id(n)]=cast_value(v,t) if t.is_integer() else v
            return t
        if isinstance(n,a.BinaryExpression):
            l=self.analyze_expression(n.left); r=self.analyze_expression(n.right)
            if l==INT_LITERAL and r.is_integer(): l=self.analyze_expression(n.left,r)
            elif r==INT_LITERAL and l.is_integer(): r=self.analyze_expression(n.right,l)
            elif l==r==INT_LITERAL and n.op in ARITH and expected and expected.is_integer():
                l=self.analyze_expression(n.left,expected); r=self.analyze_expression(n.right,expected)
            if l!=r or l==VOID or (n.op in ARITH+ORDER and not (l.is_integer() or l==INT_LITERAL)): raise SemanticError(f'Invalid operands {l}, {r}')
            t=BOOL if n.op in ORDER+EQ else l
            if n.op in (K.SLASH,K.PERCENT) and cv.get(id(n.right))==0: raise SemanticError('Division by zero')
            if id(n.left) in cv and id(n.right) in cv:
                x,y=cv[id(n.left)],cv[id(n.right)]
                ops={K.PLUS:lambda:x+y,K.MINUS:lambda:x-y,K.STAR:lambda:x*y,K.SLASH:lambda:divide(x,y),K.PERCENT:lambda:x-divide(x,y)*y,K.EQ:lambda:x==y,K.NEQ:lambda:x!=y,K.LT:lambda:x<y,K.GT:lambda:x>y,K.LTE:lambda:x<=y,K.GTE:lambda:x>=y}
                v=ops[n.op](); cv[id(n)]=cast_value(v,t) if t.is_integer() else v
            return t
        raise SemanticError('Unknown expression')
