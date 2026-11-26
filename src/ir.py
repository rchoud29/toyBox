from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from typesys import DataType


# Opcodes

class Opcode(Enum):
    # Memory
    ALLOC = "alloc"
    LOAD = "load"
    STORE = "store"

    # Arithmetic
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"

    # Logical
    NOT = "not"

    # Comparison
    EQ = "eq"
    NEQ = "neq"
    LT = "lt"
    GT = "gt"
    LTE = "lte"
    GTE = "gte"

    # Conversion
    CAST = "cast"

    # Control flow
    JMP = "jmp"
    BR = "br"

    # Functions
    CALL = "call"
    RET = "ret"


TERMINATORS = {
    Opcode.JMP,
    Opcode.BR,
    Opcode.RET,
}


# Operands

class Operand:
    pass


@dataclass(frozen=True)
class Constant(Operand):
    value: int | bool
    type: DataType

    def __str__(self) -> str:
        if isinstance(self.value, bool):
            value = str(self.value).lower()
        else:
            value = str(self.value)

        return f"{value}:{self.type}"


@dataclass(frozen=True)
class Temporary(Operand):
    index: int
    type: DataType

    def __str__(self) -> str:
        return f"%{self.index}"


@dataclass(frozen=True)
class Address(Operand):
    index: int
    type: DataType

    def __str__(self) -> str:
        return f"${self.index}"


@dataclass(frozen=True)
class IRParameter(Operand):
    name: str
    type: DataType

    def __str__(self) -> str:
        return f"%arg.{self.name}"


@dataclass(frozen=True)
class Label(Operand):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class FunctionRef(Operand):
    name: str

    def __str__(self) -> str:
        return f"@{self.name}"


# Instructions

@dataclass
class Instruction:
    opcode: Opcode
    operands: list[Operand] = field(default_factory=list)
    result: Temporary | Address | None = None

    @property
    def is_terminator(self) -> bool:
        return self.opcode in TERMINATORS

    def __str__(self) -> str:
        parts = []

        if self.result is not None:
            parts.append(
                f"{self.result}:{self.result.type} ="
            )

        parts.append(self.opcode.value)

        if self.operands:
            parts.append(
                ", ".join(str(op) for op in self.operands)
            )

        return " ".join(parts)


# Basic blocks

@dataclass
class BasicBlock:
    label: Label
    instructions: list[Instruction] = field(
        default_factory=list
    )

    @property
    def terminated(self) -> bool:
        return (
            bool(self.instructions)
            and self.instructions[-1].is_terminator
        )

    def append(self, instruction: Instruction) -> None:
        if self.terminated:
            raise IRError(
                f"Cannot append instruction to terminated "
                f"block '{self.label}'"
            )

        self.instructions.append(instruction)

    def __str__(self) -> str:
        lines = [f"{self.label}:"]

        for instruction in self.instructions:
            lines.append(f"    {instruction}")

        return "\n".join(lines)


# Functions

@dataclass
class IRFunction:
    name: str
    parameters: list[IRParameter]
    return_type: DataType

    blocks: list[BasicBlock] = field(default_factory=list)

    def append(self, block: BasicBlock) -> None:
        for existing in self.blocks:
            if existing.label == block.label:
                raise IRError(
                    f"Duplicate block '{block.label}'"
                )

        self.blocks.append(block)

    def __str__(self) -> str:
        parameters = ", ".join(
            f"{param}:{param.type}"
            for param in self.parameters
        )

        lines = [
            f"fn {self.name}({parameters}): "
            f"{self.return_type} {{"
        ]

        for block in self.blocks:
            lines.append(str(block))
            lines.append("")

        if lines[-1] == "":
            lines.pop()

        lines.append("}")

        return "\n".join(lines)


# Module

@dataclass
class IRModule:
    functions: list[IRFunction] = field(default_factory=list)

    def append(self, function: IRFunction) -> None:
        for existing in self.functions:
            if existing.name.lower() == function.name.lower():
                raise IRError(
                    f"Duplicate function '{function.name}'"
                )

        self.functions.append(function)

    def __str__(self) -> str:
        return "\n\n".join(
            str(function)
            for function in self.functions
        )


# Errors

class IRError(Exception):
    pass
