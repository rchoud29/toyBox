from dataclasses import dataclass, field
from enum import Enum
from typesys import DataType


class Opcode(Enum):
    ALLOC = 'alloc'
    LOAD = 'load'
    STORE = 'store'
    ADD = 'add'
    SUB = 'sub'
    MUL = 'mul'
    DIV = 'div'
    MOD = 'mod'
    NEG = 'neg'
    NOT = 'not'
    EQ = 'eq'
    NEQ = 'neq'
    LT = 'lt'
    GT = 'gt'
    LTE = 'lte'
    GTE = 'gte'
    CAST = 'cast'
    JMP = 'jmp'
    BR = 'br'
    CALL = 'call'
    RET = 'ret'


TERMINATORS = {Opcode.JMP, Opcode.BR, Opcode.RET}


class IRError(Exception):
    pass


class Operand:
    pass


@dataclass(frozen=True)
class Constant(Operand):
    value: int | bool
    type: DataType

    def __str__(self):
        return f'{str(self.value).lower()}:{self.type}'


@dataclass(frozen=True)
class Temporary(Operand):
    index: int
    type: DataType

    def __str__(self):
        return f'%{self.index}'


@dataclass(frozen=True)
class Address(Operand):
    index: int
    type: DataType

    def __str__(self):
        return f'${self.index}'


@dataclass(frozen=True)
class IRParameter(Operand):
    name: str
    type: DataType

    def __str__(self):
        return f'%arg.{self.name}'


@dataclass(frozen=True)
class Label(Operand):
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class FunctionRef(Operand):
    name: str

    def __str__(self):
        return '@' + self.name


@dataclass
class Instruction:
    opcode: Opcode
    operands: list[Operand] = field(default_factory=list)
    result: Temporary | Address | None = None

    @property

    def is_terminator(self):
        return self.opcode in TERMINATORS

    def __str__(self):
        parts = []
        if self.result is not None:
            parts.append(f'{self.result}:{self.result.type} =')
        parts.append(self.opcode.value)
        if self.operands:
            parts.append(', '.join(map(str, self.operands)))
        return ' '.join(parts)


@dataclass
class BasicBlock:
    label: Label
    instructions: list[Instruction] = field(default_factory=list)

    @property

    def terminated(self):
        return bool(self.instructions) and self.instructions[-1].is_terminator

    def append(self, i):
        if self.terminated:
            raise IRError('Terminated block')
        self.instructions.append(i)

    def __str__(self):
        lines = [f'{self.label}:']
        lines.extend(f'    {i}' for i in self.instructions)
        return '\n'.join(lines)


@dataclass
class IRFunction:
    name: str
    parameters: list[IRParameter]
    return_type: DataType
    blocks: list[BasicBlock] = field(default_factory=list)

    def append(self, b):
        self.blocks.append(b)

    def __str__(self):
        params = ', '.join(f'{p}:{p.type}' for p in self.parameters)
        body = '\n\n'.join(map(str, self.blocks))
        return f'fn {self.name}({params}): {self.return_type} {{\n{body}\n}}'


@dataclass
class IRModule:
    functions: list[IRFunction] = field(default_factory=list)

    def append(self, f):
        self.functions.append(f)

    def __str__(self):
        return '\n\n'.join(map(str, self.functions))
