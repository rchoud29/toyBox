from __future__ import annotations

import ast_nodes as ast

from ir import *
from typesys import DataType, VOID, INT_LITERAL
from symbols import VariableSymbol, FunctionSymbol
from semantic import SemanticAnalyzer
from tokens import TokenKind


BINARY_OPS = {
    TokenKind.PLUS: Opcode.ADD,
    TokenKind.MINUS: Opcode.SUB,
    TokenKind.STAR: Opcode.MUL,
    TokenKind.SLASH: Opcode.DIV,
    TokenKind.PERCENT: Opcode.MOD,

    TokenKind.EQ: Opcode.EQ,
    TokenKind.NEQ: Opcode.NEQ,
    TokenKind.LT: Opcode.LT,
    TokenKind.GT: Opcode.GT,
    TokenKind.LTE: Opcode.LTE,
    TokenKind.GTE: Opcode.GTE,
}

UNARY_OPS = {
    TokenKind.MINUS: Opcode.NEG,
    TokenKind.NOT: Opcode.NOT,
}


class IRGenerator:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer

        self.module = IRModule()
        self.function: IRFunction | None = None
        self.block: BasicBlock | None = None

        self.temp_count = 0
        self.addr_count = 0
        self.label_count = 0

        self.addresses: dict[int, Address] = {}

    # Operand generation

    def new_temp(self, data_type: DataType) -> Temporary:
        temp = Temporary(self.temp_count, data_type)
        self.temp_count += 1

        return temp

    def new_address(self, data_type: DataType) -> Address:
        address = Address(self.addr_count, data_type)
        self.addr_count += 1

        return address

    def new_label(self, prefix: str) -> Label:
        label = Label(f"{prefix}.{self.label_count}")
        self.label_count += 1

        return label

    # Block management

    def new_block(self, label: Label) -> BasicBlock:
        block = BasicBlock(label)
        self.function.append(block)

        return block

    def set_block(self, block: BasicBlock) -> None:
        self.block = block

    def terminated(self) -> bool:
        return self.block is None or self.block.terminated

    # Instruction generation

    def emit(
        self,
        opcode: Opcode,
        operands: list[Operand] | None = None,
        result: Temporary | Address | None = None
    ) -> None:

        if self.block is None:
            raise IRError("No active basic block")

        instruction = Instruction(
            opcode,
            operands if operands is not None else [],
            result
        )

        self.block.append(instruction)

    def emit_value(
        self,
        opcode: Opcode,
        data_type: DataType,
        operands: list[Operand]
    ) -> Temporary:

        result = self.new_temp(data_type)

        self.emit(opcode, operands, result)

        return result

    def emit_jump(self, label: Label) -> None:
        self.emit(Opcode.JMP, [label])

    def emit_branch(
        self,
        condition: Operand,
        true_label: Label,
        false_label: Label
    ) -> None:

        self.emit(
            Opcode.BR,
            [condition, true_label, false_label]
        )

    # Semantic information

    def get_type(self, node: ast.Expression) -> DataType:
        try:
            return self.analyzer.expression_types[id(node)]

        except KeyError:
            raise IRError(
                f"Missing type for {type(node).__name__}"
            )

    def get_symbol(self, node: ast.Node):
        try:
            return self.analyzer.resolved_symbols[id(node)]

        except KeyError:
            raise IRError(
                f"Missing symbol for {type(node).__name__}"
            )

    def get_address(self, node: ast.Node) -> Address:
        symbol = self.get_symbol(node)

        try:
            return self.addresses[id(symbol)]

        except KeyError:
            raise IRError(
                f"No storage allocated for '{symbol.name}'"
            )

    # Memory management

    def allocate(self, symbol: VariableSymbol) -> Address:
        address = self.new_address(symbol.type)

        self.addresses[id(symbol)] = address

        # All local allocations belong to the entry block.
        # Insert them before executable instructions.

        entry = self.function.blocks[0]

        instruction = Instruction(
            Opcode.ALLOC,
            result=address
        )

        index = 0

        while (
            index < len(entry.instructions)
            and entry.instructions[index].opcode == Opcode.ALLOC
        ):
            index += 1

        entry.instructions.insert(index, instruction)

        return address

    def load(self, address: Address) -> Temporary:
        return self.emit_value(
            Opcode.LOAD,
            address.type,
            [address]
        )

    def store(
        self,
        value: Operand,
        address: Address
    ) -> None:

        self.emit(
            Opcode.STORE,
            [value, address]
        )

    # Program generation

    def generate(self, program: ast.Program) -> IRModule:
        self.module = IRModule()

        for function in program.functions:
            self.generate_function(function)

        return self.module

    def generate_function(self, node: ast.Function) -> None:
        symbol = self.get_symbol(node)

        if not isinstance(symbol, FunctionSymbol):
            raise IRError("Expected function symbol")

        # Reset function-local state.

        self.temp_count = 0
        self.addr_count = 0
        self.label_count = 0
        self.addresses = {}

        parameters = [
            IRParameter(param.name.lower(), param.type)
            for param in symbol.parameters
        ]

        self.function = IRFunction(
            symbol.name.lower(),
            parameters,
            symbol.return_type
        )

        self.module.append(self.function)

        entry = self.new_block(Label("entry"))
        self.set_block(entry)

        # Copy incoming parameters into mutable storage.

        for parameter, param_symbol in zip(
            parameters,
            symbol.parameters
        ):
            address = self.allocate(param_symbol)
            self.store(parameter, address)

        self.generate_block(node.body)

        if not self.terminated():
            if symbol.return_type == VOID:
                self.emit(Opcode.RET)

            else:
                raise IRError(
                    f"Function '{node.name}' has no return"
                )

        self.function = None
        self.block = None

    def generate_block(self, node: ast.Block) -> None:
        for statement in node.statements:
            if self.terminated():
                break

            self.generate_statement(statement)

    # Statement generation

    def generate_statement(self, node: ast.Statement) -> None:
        match node:
            case ast.Declaration():
                self.generate_declaration(node)

            case ast.Assignment():
                self.generate_assignment(node)

            case ast.Return():
                self.generate_return(node)

            case ast.If():
                self.generate_if(node)

            case ast.While():
                self.generate_while(node)

            case ast.CallStatement():
                self.generate_call(node.call)

            case _:
                raise IRError(
                    f"Unknown statement "
                    f"{type(node).__name__}"
                )

    def generate_declaration(
        self,
        node: ast.Declaration
    ) -> None:

        symbol = self.get_symbol(node)

        value = self.generate_expression(node.value)
        address = self.allocate(symbol)

        self.store(value, address)

    def generate_assignment(
        self,
        node: ast.Assignment
    ) -> None:

        address = self.get_address(node)
        value = self.generate_expression(node.value)

        self.store(value, address)

    def generate_return(self, node: ast.Return) -> None:
        if node.value is None:
            self.emit(Opcode.RET)

        else:
            value = self.generate_expression(node.value)

            self.emit(Opcode.RET, [value])

    # Conditional branching

    def generate_if(self, node: ast.If) -> None:
        condition = self.generate_expression(node.condition)

        true_label = self.new_label("if.true")
        end_label = self.new_label("if.end")

        false_label = (
            self.new_label("if.false")
            if node.else_body is not None
            else end_label
        )

        self.emit_branch(
            condition,
            true_label,
            false_label
        )

        # True branch

        true_block = self.new_block(true_label)
        self.set_block(true_block)

        self.generate_block(node.body)

        true_falls_through = not self.terminated()

        if true_falls_through:
            self.emit_jump(end_label)

        # False branch

        false_falls_through = node.else_body is None

        if node.else_body is not None:
            false_block = self.new_block(false_label)
            self.set_block(false_block)

            if isinstance(node.else_body, ast.Block):
                self.generate_block(node.else_body)

            elif isinstance(node.else_body, ast.If):
                self.generate_if(node.else_body)

            false_falls_through = not self.terminated()

            if false_falls_through:
                self.emit_jump(end_label)

        # Only create a merge block if it is reachable.

        if true_falls_through or false_falls_through:
            end_block = self.new_block(end_label)
            self.set_block(end_block)

        else:
            self.block = None

    # Loops

    def generate_while(self, node: ast.While) -> None:
        condition_label = self.new_label("while.cond")
        body_label = self.new_label("while.body")
        end_label = self.new_label("while.end")

        self.emit_jump(condition_label)

        # Condition block

        condition_block = self.new_block(condition_label)
        self.set_block(condition_block)

        condition = self.generate_expression(node.condition)

        self.emit_branch(
            condition,
            body_label,
            end_label
        )

        # Body block

        body_block = self.new_block(body_label)
        self.set_block(body_block)

        self.generate_block(node.body)

        if not self.terminated():
            self.emit_jump(condition_label)

        # Exit block

        end_block = self.new_block(end_label)
        self.set_block(end_block)

    # Expression generation

    def generate_expression(
        self,
        node: ast.Expression
    ) -> Operand:

        data_type = self.get_type(node)

        # Materialize compile-time constants directly.

        if id(node) in self.analyzer.constant_values:
            value = self.analyzer.constant_values[id(node)]

            if data_type == INT_LITERAL:
                raise IRError(
                    "Unresolved integer literal reached IR"
                )

            return Constant(value, data_type)

        match node:
            case ast.Identifier():
                return self.generate_identifier(node)

            case ast.BinaryExpression():
                return self.generate_binary(node)

            case ast.UnaryExpression():
                return self.generate_unary(node)

            case ast.Cast():
                return self.generate_cast(node)

            case ast.Call():
                result = self.generate_call(node)

                if result is None:
                    raise IRError(
                        "Void call cannot produce a value"
                    )

                return result

            case _:
                raise IRError(
                    f"Unknown expression "
                    f"{type(node).__name__}"
                )

    def generate_identifier(
        self,
        node: ast.Identifier
    ) -> Temporary:

        address = self.get_address(node)

        return self.load(address)

    def generate_binary(
        self,
        node: ast.BinaryExpression
    ) -> Temporary:

        left = self.generate_expression(node.left)
        right = self.generate_expression(node.right)

        opcode = BINARY_OPS[node.op]
        data_type = self.get_type(node)

        return self.emit_value(
            opcode,
            data_type,
            [left, right]
        )

    def generate_unary(
        self,
        node: ast.UnaryExpression
    ) -> Temporary:

        operand = self.generate_expression(node.operand)

        opcode = UNARY_OPS[node.op]
        data_type = self.get_type(node)

        return self.emit_value(
            opcode,
            data_type,
            [operand]
        )

    def generate_cast(
        self,
        node: ast.Cast
    ) -> Operand:

        value = self.generate_expression(node.value)
        destination = self.get_type(node)

        # No conversion needed for identical types.

        if value.type == destination:
            return value

        return self.emit_value(
            Opcode.CAST,
            destination,
            [value]
        )

    def generate_call(
        self,
        node: ast.Call
    ) -> Temporary | None:

        symbol = self.get_symbol(node)

        if not isinstance(symbol, FunctionSymbol):
            raise IRError("Expected function symbol")

        arguments = [
            self.generate_expression(argument)
            for argument in node.arguments
        ]

        operands = [
            FunctionRef(symbol.name.lower()),
            *arguments
        ]

        if symbol.return_type == VOID:
            self.emit(Opcode.CALL, operands)

            return None

        return self.emit_value(
            Opcode.CALL,
            symbol.return_type,
            operands
        )
