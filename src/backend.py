import ir
from typesys import VOID,BOOL
O=ir.Opcode
ARG_REGISTERS=('rdi','rsi','rdx','rcx','r8','r9')
class BackendError(Exception): pass
class Backend:
    def emit(self,s): self.lines.append('    '+s)
    def label(self,s): self.lines.append(s+':')
    def validate_type(self,t):
        if t not in (VOID,BOOL) and not (t.is_integer() and 1<=t.width<=64): raise BackendError(f'Unsupported native type {t}')
    def generate(self,module):
        self.lines=['bits 64','section .text','global _start']; self.count=0
        fs={f.name:f for f in module.functions}; m=fs.get('main')
        if m is None or m.parameters or (m.return_type!=VOID and not m.return_type.is_integer()): raise BackendError('Expected parameterless integer or void main')
        self.label('_start'); self.emit('call fn_main'); self.emit('xor edi, edi' if m.return_type==VOID else 'mov rdi, rax'); self.emit('mov eax, 60'); self.emit('syscall')
        for f in module.functions: self.generate_function(f)
        return '\n'.join(self.lines)+'\n'
    def slot(self,v): return f'qword [rbp - {self.slots[v]}]'
    def load(self,v,r='rax'):
        if isinstance(v,ir.Constant): self.validate_type(v.type); self.emit(f'mov {r}, {int(v.value)}')
        else: self.emit(f'mov {r}, {self.slot(v)}')
    def normalize(self,r,t):
        self.validate_type(t)
        if t==BOOL: self.emit(f'and {r}, 1')
        elif t.width<64:
            n=64-t.width; self.emit(f'shl {r}, {n}'); self.emit(f'{"sar" if t.signed else "shr"} {r}, {n}')
    def save(self,i): self.normalize('rax',i.result.type); self.emit(f'mov {self.slot(i.result)}, rax')
    def generate_function(self,f):
        self.validate_type(f.return_type); self.slots={}; self.function=f
        values=list(f.parameters)+[i.result for b in f.blocks for i in b.instructions if i.result is not None]
        for v in values:
            self.validate_type(v.type)
            if v not in self.slots: self.slots[v]=8*(len(self.slots)+1)
        size=((len(self.slots)*8+15)//16)*16
        self.label('fn_'+f.name); self.emit('push rbp'); self.emit('mov rbp, rsp')
        if size: self.emit(f'sub rsp, {size}')
        for j,p in enumerate(f.parameters):
            r=ARG_REGISTERS[j] if j<6 else f'qword [rbp + {16+8*(j-6)}]'
            self.emit(f'mov rax, {r}'); self.normalize('rax',p.type); self.emit(f'mov {self.slot(p)}, rax')
        for b in f.blocks:
            if not b.terminated: raise BackendError('Unterminated block')
            self.label('.block_'+b.label.name)
            for i in b.instructions: self.generate_instruction(i)
        self.label('.return'); self.emit('mov rsp, rbp'); self.emit('pop rbp'); self.emit('ret')
    def generate_instruction(self,i):
        op=i.opcode; a=i.operands; self.emit('; '+str(i))
        if op==O.ALLOC: return
        if op==O.LOAD: self.load(a[0]); self.save(i)
        elif op==O.STORE: self.load(a[0]); self.normalize('rax',a[1].type); self.emit(f'mov {self.slot(a[1])}, rax')
        elif op in (O.ADD,O.SUB,O.MUL):
            self.load(a[0]); self.load(a[1],'rcx'); self.emit(f'{ {O.ADD:"add",O.SUB:"sub",O.MUL:"imul"}[op]} rax, rcx'); self.save(i)
        elif op in (O.DIV,O.MOD):
            self.load(a[0]); self.load(a[1],'rcx'); n=self.count; self.count+=1
            self.emit('test rcx, rcx'); self.emit(f'jnz .nonzero{n}'); self.emit('ud2'); self.label(f'.nonzero{n}')
            if a[0].type.signed:
                self.emit('cmp rcx, -1'); self.emit(f'jne .divide{n}'); self.emit('neg rax'); self.emit('xor edx, edx'); self.emit(f'jmp .done{n}'); self.label(f'.divide{n}'); self.emit('cqo'); self.emit('idiv rcx'); self.label(f'.done{n}')
            else: self.emit('xor edx, edx'); self.emit('div rcx')
            if op==O.MOD: self.emit('mov rax, rdx')
            self.save(i)
        elif op in (O.NEG,O.NOT): self.load(a[0]); self.emit('neg rax' if op==O.NEG else 'xor rax, 1'); self.save(i)
        elif op in (O.EQ,O.NEQ,O.LT,O.LTE,O.GT,O.GTE):
            self.load(a[0]); self.load(a[1],'rcx'); self.emit('cmp rax, rcx')
            codes={O.EQ:'e',O.NEQ:'ne',O.LT:'l',O.LTE:'le',O.GT:'g',O.GTE:'ge'} if a[0].type.signed else {O.EQ:'e',O.NEQ:'ne',O.LT:'b',O.LTE:'be',O.GT:'a',O.GTE:'ae'}
            self.emit('set'+codes[op]+' al'); self.emit('movzx rax, al'); self.save(i)
        elif op==O.CAST:
            self.load(a[0])
            if i.result.type==BOOL: self.emit('test rax, rax'); self.emit('setne al'); self.emit('movzx rax, al')
            self.save(i)
        elif op==O.JMP: self.emit('jmp .block_'+a[0].name)
        elif op==O.BR: self.load(a[0]); self.emit('test rax, rax'); self.emit('jnz .block_'+a[1].name); self.emit('jmp .block_'+a[2].name)
        elif op==O.CALL:
            args=a[1:]; extra=args[6:]; pad=8*(len(extra)%2)
            if pad: self.emit('sub rsp, 8')
            for v in reversed(extra): self.load(v); self.emit('push rax')
            for r,v in zip(ARG_REGISTERS,args): self.load(v,r)
            self.emit('call fn_'+a[0].name)
            if extra: self.emit(f'add rsp, {8*len(extra)+pad}')
            if i.result is not None: self.save(i)
        elif op==O.RET:
            if a: self.load(a[0]); self.normalize('rax',self.function.return_type)
            self.emit('jmp .return')
        else: raise BackendError(f'Unknown opcode {op}')
