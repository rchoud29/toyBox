from __future__ import annotations

import ir

from typesys import DataType, TypeKind, VOID


ARG_REGISTERS = (
    "rdi",
    "rsi",
    "rdx",
    "rcx",
    "r8",
    "r9",
)

ARITHMETIC_OPS = {
    ir.Opcode.ADD: "add",
    ir.Opcode.SUB: "sub",
    ir.Opcode.MUL: "imul",
}

SIGNED_COMPARISONS = {
    ir.Opcode.EQ: "sete",
    ir.Opcode.NEQ: "setne",
    ir.Opcode.LT: "setl",
    ir.Opcode.LTE: "setle",
    ir.Opcode.GT: "setg",
    ir.Opcode.GTE: "setge",
}

UNSIGNED_COMPARISONS = {
    ir.Opcode.EQ: "sete",
    ir.Opcode.NEQ: "setne",
    ir.Opcode.LT: "setb",
    ir.Opcode.LTE: "setbe",
    ir.Opcode.GT: "seta",
    ir.Opcode.GTE: "setae",
}


class Backend:
    def __init__(self):
        self.lines: list[str] = []

        self.function: ir.IRFunction | None = None

        self.slots: dict[ir.Operand, int] = {}
        self.stack_size = 0

        self.functions: dict[str, ir.IRFunction] = {}

        self.label_count = 0

    # Assembly generation

    def emit(self, instruction: str = "") -> None:
        if instruction:
            self.lines.append(f"    {instruction}")
        else:
            self.lines.append("")

    def emit_label(self, label: str) -> None:
        self.lines.append(f"{label}:")

    def new_label(self, prefix: str) -> str:
        label = f".internal_{prefix}_{self.label_count}"
        self.label_count += 1

        return label

    def function_label(self, name: str) -> str:
        return f"fn_{name.lower()}"

    def block_label(self, label: ir.Label) -> str:
        return f".block_{label.name}"

    # Type validation

    def validate_type(self, data_type: DataType) -> None:
        if data_type == VOID:
            return

        if data_type.kind == TypeKind.BOOL:
            return

        if (
            data_type.kind == TypeKind.INT
            and 1 <= data_type.width <= 64
        ):
            return

        raise BackendError(
            f"Unsupported native type '{data_type}'"
        )

    # Stack management

    def allocate_slot(self, operand: ir.Operand) -> None:
        if operand in self.slots:
            return

        self.validate_type(operand.type)

        self.stack_size += 8
        self.slots[operand] = self.stack_size

    def get_slot(self, operand: ir.Operand) -> str:
        if operand not in self.slots:
            raise BackendError(
                f"No stack slot for {operand}"
            )

        return f"qword [rbp - {self.slots[operand]}]"

    def prepare_stack(self, function: ir.IRFunction) -> None:
        self.slots = {}
        self.stack_size = 0

        for parameter in function.parameters:
            self.allocate_slot(parameter)

        for block in function.blocks:
            for instruction in block.instructions:
                if instruction.result is not None:
                    self.allocate_slot(instruction.result)

                for operand in instruction.operands:
                    if isinstance(operand, ir.Constant):
                        self.validate_type(operand.type)

        # System V requires 16-byte stack alignment
        # immediately before a call.

        self.stack_size = (
            (self.stack_size + 15) // 16
        ) * 16

    # Operand access

    def load_operand(
        self,
        operand: ir.Operand,
        register: str
    ) -> None:

        if isinstance(operand, ir.Constant):
            self.validate_type(operand.type)

            value = int(operand.value)

            self.emit(f"mov {register}, {value}")

            return

        if isinstance(
            operand,
            (ir.Temporary, ir.IRParameter)
        ):
            self.emit(
                f"mov {register}, {self.get_slot(operand)}"
            )

            return

        raise BackendError(
            f"Cannot load operand {operand}"
        )

    def save_result(
        self,
        instruction: ir.Instruction,
        register: str = "rax"
    ) -> None:

        if instruction.result is None:
            raise BackendError(
                f"{instruction.opcode.value} has no result"
            )

        self.normalize(register, instruction.result.type)

        self.emit(
            f"mov {self.get_slot(instruction.result)}, "
            f"{register}"
        )

    # Integer representation

    def normalize(
        self,
        register: str,
        data_type: DataType
    ) -> None:

        self.validate_type(data_type)

        if data_type.kind == TypeKind.BOOL:
            self.emit(f"and {register}, 1")
            return

        if data_type.kind != TypeKind.INT:
            raise BackendError(
                f"Cannot normalize {data_type}"
            )

        if data_type.width == 64:
            return

        shift = 64 - data_type.width

        self.emit(f"shl {register}, {shift}")

        if data_type.signed:
            self.emit(f"sar {register}, {shift}")
        else:
            self.emit(f"shr {register}, {shift}")

    # Module generation

    def generate(self, module: ir.IRModule) -> str:
        self.lines = []
        self.label_count = 0

        self.functions = {
            function.name.lower(): function
            for function in module.functions
        }

        self.validate_entry_point()

        self.lines.append("bits 64")
        self.lines.append("section .text")
        self.lines.append("global _start")
        self.emit()

        self.generate_entry_point()

        for function in module.functions:
            self.generate_function(function)

        return "\n".join(self.lines) + "\n"

    def validate_entry_point(self) -> None:
        if "main" not in self.functions:
            raise BackendError("Missing main function")

        main = self.functions["main"]

        if main.parameters:
            raise BackendError(
                "main cannot accept parameters yet"
            )

        self.validate_type(main.return_type)

        if (
            main.return_type != VOID
            and not main.return_type.is_integer()
        ):
            raise BackendError(
                "main must return an integer or void"
            )

    def generate_entry_point(self) -> None:
        main = self.functions["main"]

        self.emit_label("_start")

        self.emit("call fn_main")

        if main.return_type == VOID:
            self.emit("xor edi, edi")
        else:
            self.emit("mov rdi, rax")

        # Linux exit syscall.
        self.emit("mov eax, 60")
        self.emit("syscall")
        self.emit()

    # Function generation

    def generate_function(
        self,
        function: ir.IRFunction
    ) -> None:

        self.function = function

        self.validate_type(function.return_type)
        self.prepare_stack(function)

        self.emit_label(
            self.function_label(function.name)
        )

        # Function prologue.

        self.emit("push rbp")
        self.emit("mov rbp, rsp")

        if self.stack_size:
            self.emit(f"sub rsp, {self.stack_size}")

        # Save incoming arguments.

        for index, parameter in enumerate(
            function.parameters
        ):
            if index < len(ARG_REGISTERS):
                register = ARG_REGISTERS[index]

                self.emit(f"mov rax, {register}")

            else:
                offset = 16 + (
                    index - len(ARG_REGISTERS)
                ) * 8

                self.emit(
                    f"mov rax, qword [rbp + {offset}]"
                )

            self.normalize("rax", parameter.type)

            self.emit(
                f"mov {self.get_slot(parameter)}, rax"
            )

        # Generate basic blocks.

        for block in function.blocks:
            self.generate_block(block)

        # Shared function epilogue.

        self.emit_label(".return")
        self.emit("mov rsp, rbp")
        self.emit("pop rbp")
        self.emit("ret")
        self.emit()

        self.function = None

    def generate_block(
        self,
        block: ir.BasicBlock
    ) -> None:

        if not block.terminated:
            raise BackendError(
                f"Block '{block.label}' has no terminator"
            )

        self.emit_label(
            self.block_label(block.label)
        )

        for instruction in block.instructions:
            self.generate_instruction(instruction)

    # Instruction dispatch

    def generate_instruction(
        self,
        instruction: ir.Instruction
    ) -> None:

        opcode = instruction.opcode

        self.emit(f"; {instruction}")

        if opcode == ir.Opcode.ALLOC:
            self.generate_alloc(instruction)

        elif opcode == ir.Opcode.LOAD:
            self.generate_load(instruction)

        elif opcode == ir.Opcode.STORE:
            self.generate_store(instruction)

        elif opcode in ARITHMETIC_OPS:
            self.generate_arithmetic(instruction)

        elif opcode in (
            ir.Opcode.DIV,
            ir.Opcode.MOD
        ):
            self.generate_division(instruction)

        elif opcode == ir.Opcode.NEG:
            self.generate_neg(instruction)

        elif opcode == ir.Opcode.NOT:
            self.generate_not(instruction)

        elif opcode in SIGNED_COMPARISONS:
            self.generate_comparison(instruction)

        elif opcode == ir.Opcode.CAST:
            self.generate_cast(instruction)

        elif opcode == ir.Opcode.JMP:
            self.generate_jump(instruction)

        elif opcode == ir.Opcode.BR:
            self.generate_branch(instruction)

        elif opcode == ir.Opcode.CALL:
            self.generate_call(instruction)

        elif opcode == ir.Opcode.RET:
            self.generate_return(instruction)

        else:
            raise BackendError(
                f"Unsupported opcode {opcode}"
            )

    # Memory instructions

    def generate_alloc(
        self,
        instruction: ir.Instruction
    ) -> None:

        # Storage was reserved in prepare_stack().
        pass

    def generate_load(
        self,
        instruction: ir.Instruction
    ) -> None:

        address = instruction.operands[0]

        self.emit(
            f"mov rax, {self.get_slot(address)}"
        )

        self.save_result(instruction)

    def generate_store(
        self,
        instruction: ir.Instruction
    ) -> None:

        value, address = instruction.operands

        self.load_operand(value, "rax")
        self.normalize("rax", address.type)

        self.emit(
            f"mov {self.get_slot(address)}, rax"
        )

    # Arithmetic instructions

    def generate_arithmetic(
        self,
        instruction: ir.Instruction
    ) -> None:

        left, right = instruction.operands

        self.load_operand(left, "rax")
        self.load_operand(right, "rcx")

        opcode = ARITHMETIC_OPS[instruction.opcode]

        self.emit(f"{opcode} rax, rcx")

        self.save_result(instruction)

    def generate_division(
        self,
        instruction: ir.Instruction
    ) -> None:

        left, right = instruction.operands

        self.load_operand(left, "rax")
        self.load_operand(right, "rcx")

        nonzero = self.new_label("div_nonzero")

        # Trap on division by zero.

        self.emit("test rcx, rcx")
        self.emit(f"jnz {nonzero}")
        self.emit("ud2")

        self.emit_label(nonzero)

        if left.type.signed:
            normal = self.new_label("div_normal")
            done = self.new_label("div_done")

            # Handle division by -1 separately.
            # This avoids an x86 overflow exception
            # for the minimum signed 64-bit integer.

            self.emit("cmp rcx, -1")
            self.emit(f"jne {normal}")

            self.emit("neg rax")
            self.emit("xor edx, edx")
            self.emit(f"jmp {done}")

            self.emit_label(normal)

            # Sign-extend RAX into RDX:RAX.
            self.emit("cqo")
            self.emit("idiv rcx")

            self.emit_label(done)

        else:
            self.emit("xor edx, edx")
            self.emit("div rcx")

        if instruction.opcode == ir.Opcode.MOD:
            self.emit("mov rax, rdx")

        self.save_result(instruction)

    def generate_neg(
        self,
        instruction: ir.Instruction
    ) -> None:

        operand = instruction.operands[0]

        self.load_operand(operand, "rax")

        self.emit("neg rax")

        self.save_result(instruction)

    def generate_not(
        self,
        instruction: ir.Instruction
    ) -> None:

        operand = instruction.operands[0]

        self.load_operand(operand, "rax")

        self.emit("xor rax, 1")

        self.save_result(instruction)

    # Comparisons

    def generate_comparison(
        self,
        instruction: ir.Instruction
    ) -> None:

        left, right = instruction.operands

        self.load_operand(left, "rax")
        self.load_operand(right, "rcx")

        self.emit("cmp rax, rcx")

        if left.type.signed:
            opcode = SIGNED_COMPARISONS[
                instruction.opcode
            ]
        else:
            opcode = UNSIGNED_COMPARISONS[
                instruction.opcode
            ]

        self.emit(f"{opcode} al")
        self.emit("movzx rax, al")

        self.save_result(instruction)

    # Casting

    def generate_cast(
        self,
        instruction: ir.Instruction
    ) -> None:

        operand = instruction.operands[0]
        destination = instruction.result.type

        self.load_operand(operand, "rax")

        if destination.kind == TypeKind.BOOL:
            self.emit("test rax, rax")
            self.emit("setne al")
            self.emit("movzx rax, al")

        # Integer narrowing, widening and signedness
        # changes are handled by save_result().

        self.save_result(instruction)

    # Control flow

    def generate_jump(
        self,
        instruction: ir.Instruction
    ) -> None:

        label = instruction.operands[0]

        self.emit(
            f"jmp {self.block_label(label)}"
        )

    def generate_branch(
        self,
        instruction: ir.Instruction
    ) -> None:

        condition, true_label, false_label = (
            instruction.operands
        )

        self.load_operand(condition, "rax")

        self.emit("test rax, rax")

        self.emit(
            f"jnz {self.block_label(true_label)}"
        )

        self.emit(
            f"jmp {self.block_label(false_label)}"
        )

    # Function calls

    def generate_call(
        self,
        instruction: ir.Instruction
    ) -> None:

        function = instruction.operands[0]
        arguments = instruction.operands[1:]

        if function.name.lower() not in self.functions:
            raise BackendError(
                f"Unknown function '{function.name}'"
            )

        register_args = arguments[:len(ARG_REGISTERS)]
        stack_args = arguments[len(ARG_REGISTERS):]

        # Preserve 16-byte alignment before CALL.

        padding = 8 if len(stack_args) % 2 else 0

        if padding:
            self.emit("sub rsp, 8")

        # Stack arguments are pushed right-to-left.

        for argument in reversed(stack_args):
            self.load_operand(argument, "rax")
            self.emit("push rax")

        # Load register arguments.

        for register, argument in zip(
            ARG_REGISTERS,
            register_args
        ):
            self.load_operand(argument, register)

        self.emit(
            f"call {self.function_label(function.name)}"
        )

        # Caller removes stack arguments.

        cleanup = len(stack_args) * 8 + padding

        if cleanup:
            self.emit(f"add rsp, {cleanup}")

        if instruction.result is not None:
            self.save_result(instruction)

    def generate_return(
        self,
        instruction: ir.Instruction
    ) -> None:

        if instruction.operands:
            value = instruction.operands[0]

            self.load_operand(value, "rax")

            self.normalize(
                "rax",
                self.function.return_type
            )

        self.emit("jmp .return")


class BackendError(Exception):
    pass
