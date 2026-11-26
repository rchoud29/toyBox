from ast_nodes import *
from typesys import *
from symbols import *
from tokens import TokenKind


class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = Scope()
        self.scope = self.global_scope

        self.current_function: FunctionSymbol | None = None

        self.expression_types: dict[int, DataType] = {}
        self.resolved_symbols: dict[int, Symbol] = {}
        self.constant_values: dict[int, int | bool] = {}

    # Scope management

    def enter_scope(self) -> None:
        self.scope = Scope(self.scope)

    def exit_scope(self) -> None:
        if self.scope.parent is None:
            raise SemanticError("Cannot exit global scope")

        self.scope = self.scope.parent

    # Type and symbol resolution

    def resolve_type(self, node: Type) -> DataType:
        try:
            return resolve_type(node.name)

        except TypeError as error:
            raise SemanticError(str(error)) from error

    def resolve_symbol(self, name: str) -> Symbol:
        try:
            return self.scope.resolve(name)

        except SymbolError as error:
            raise SemanticError(str(error)) from error

    def define_symbol(self, symbol: Symbol) -> None:
        try:
            self.scope.define(symbol)

        except SymbolError as error:
            raise SemanticError(str(error)) from error

    def require_type(
        self,
        actual: DataType,
        expected: DataType
    ) -> None:
        if actual != expected:
            raise SemanticError(
                f"Expected {expected}, got {actual}"
            )

    # Program analysis

    def analyze(self, program: Program) -> Program:
        self.global_scope = Scope()
        self.scope = self.global_scope
        self.current_function = None

        self.expression_types.clear()
        self.resolved_symbols.clear()
        self.constant_values.clear()

        # Pass 1: Register function signatures.

        for function in program.functions:
            self.register_function(function)

        # Pass 2: Analyze function bodies.

        for function in program.functions:
            self.analyze_function(function)

        return program

    def register_function(self, node: Function) -> None:
        return_type = self.resolve_type(node.return_type)

        parameters = []
        names = set()

        for param in node.parameters:
            data_type = self.resolve_type(param.type)

            if data_type == VOID:
                raise SemanticError(
                    f"Parameter '{param.name}' cannot be void"
                )

            name = param.name.lower()

            if name in names:
                raise SemanticError(
                    f"Duplicate parameter '{param.name}'"
                )

            names.add(name)

            symbol = VariableSymbol(param.name, data_type)

            parameters.append(symbol)
            self.resolved_symbols[id(param)] = symbol

        symbol = FunctionSymbol(
            node.name,
            parameters,
            return_type
        )

        self.define_symbol(symbol)
        self.resolved_symbols[id(node)] = symbol

    def analyze_function(self, node: Function) -> None:
        symbol = self.resolve_symbol(node.name)

        if not isinstance(symbol, FunctionSymbol):
            raise SemanticError(
                f"'{node.name}' is not a function"
            )

        self.current_function = symbol
        self.enter_scope()

        try:
            for param in symbol.parameters:
                self.define_symbol(param)

            self.analyze_block(node.body, new_scope=False)

            if (
                symbol.return_type != VOID
                and not self.block_returns(node.body)
            ):
                raise SemanticError(
                    f"Function '{node.name}' does not "
                    f"return on every path"
                )

        finally:
            self.exit_scope()
            self.current_function = None

    def analyze_block(
        self,
        node: Block,
        new_scope: bool = True
    ) -> None:

        if new_scope:
            self.enter_scope()

        try:
            for statement in node.statements:
                self.analyze_statement(statement)

        finally:
            if new_scope:
                self.exit_scope()

    # Statement analysis

    def analyze_statement(self, node: Statement) -> None:
        match node:
            case Declaration():
                self.analyze_declaration(node)

            case Assignment():
                self.analyze_assignment(node)

            case Return():
                self.analyze_return(node)

            case If():
                self.analyze_if(node)

            case While():
                self.analyze_while(node)

            case CallStatement():
                self.analyze_expression(node.call)

            case _:
                raise SemanticError(
                    f"Unknown statement: "
                    f"{type(node).__name__}"
                )

    def analyze_declaration(self, node: Declaration) -> None:
        data_type = self.resolve_type(node.type)

        if data_type == VOID:
            raise SemanticError(
                f"Variable '{node.name}' cannot be void"
            )

        self.analyze_expression(node.value, data_type)

        symbol = VariableSymbol(node.name, data_type)

        self.define_symbol(symbol)
        self.resolved_symbols[id(node)] = symbol

    def analyze_assignment(self, node: Assignment) -> None:
        symbol = self.resolve_symbol(node.name)

        if not isinstance(symbol, VariableSymbol):
            raise SemanticError(
                f"Cannot assign to '{node.name}'"
            )

        self.analyze_expression(node.value, symbol.type)

        self.resolved_symbols[id(node)] = symbol

    def analyze_return(self, node: Return) -> None:
        if self.current_function is None:
            raise SemanticError(
                "Return outside of function"
            )

        return_type = self.current_function.return_type

        if return_type == VOID:
            if node.value is not None:
                raise SemanticError(
                    "Void function cannot return a value"
                )

            return

        if node.value is None:
            raise SemanticError(
                f"Expected return value of type {return_type}"
            )

        self.analyze_expression(node.value, return_type)

    def analyze_if(self, node: If) -> None:
        self.analyze_expression(node.condition, BOOL)

        self.analyze_block(node.body)

        if isinstance(node.else_body, Block):
            self.analyze_block(node.else_body)

        elif isinstance(node.else_body, If):
            self.analyze_if(node.else_body)

    def analyze_while(self, node: While) -> None:
        self.analyze_expression(node.condition, BOOL)
        self.analyze_block(node.body)

    # Expression analysis

    def analyze_expression(
        self,
        node: Expression,
        expected: DataType | None = None
    ) -> DataType:

        match node:
            case Integer():
                result = self.analyze_integer(node, expected)

            case Boolean():
                result = BOOL
                self.constant_values[id(node)] = node.value

            case Identifier():
                result = self.analyze_identifier(node)

            case BinaryExpression():
                result = self.analyze_binary(node, expected)

            case UnaryExpression():
                result = self.analyze_unary(node, expected)

            case Call():
                result = self.analyze_call(node)

            case Cast():
                result = self.analyze_cast(node)

            case _:
                raise SemanticError(
                    f"Unknown expression: "
                    f"{type(node).__name__}"
                )

        if expected is not None:
            self.require_type(result, expected)

        self.expression_types[id(node)] = result

        return result

    # Integer literals

    def analyze_integer(
        self,
        node: Integer,
        expected: DataType | None
    ) -> DataType:

        self.constant_values[id(node)] = node.value

        if expected is None or expected == INT_LITERAL:
            return INT_LITERAL

        if not expected.is_integer():
            raise SemanticError(
                f"Integer literal cannot be used as {expected}"
            )

        if not expected.fits(node.value):
            raise SemanticError(
                f"Integer {node.value} does not fit in "
                f"{expected} "
                f"({expected.minimum} to {expected.maximum})"
            )

        return expected

    # Identifiers

    def analyze_identifier(self, node: Identifier) -> DataType:
        symbol = self.resolve_symbol(node.name)

        if not isinstance(symbol, VariableSymbol):
            raise SemanticError(
                f"'{node.name}' is not a variable"
            )

        self.resolved_symbols[id(node)] = symbol

        return symbol.type

    # Binary expressions

    def analyze_binary(
        self,
        node: BinaryExpression,
        expected: DataType | None
    ) -> DataType:

        arithmetic = (
            TokenKind.PLUS,
            TokenKind.MINUS,
            TokenKind.STAR,
            TokenKind.SLASH,
            TokenKind.PERCENT
        )

        comparison = (
            TokenKind.LT,
            TokenKind.GT,
            TokenKind.LTE,
            TokenKind.GTE
        )

        equality = (
            TokenKind.EQ,
            TokenKind.NEQ
        )

        if node.op not in arithmetic + comparison + equality:
            raise SemanticError(
                f"Unknown binary operator {node.op.name}"
            )

        # Initially resolve both operand types.

        left = self.analyze_expression(node.left)
        right = self.analyze_expression(node.right)

        # Resolve untyped literals using the other operand.

        if left == INT_LITERAL and right.is_integer():
            left = self.analyze_expression(node.left, right)

        elif right == INT_LITERAL and left.is_integer():
            right = self.analyze_expression(node.right, left)

        # Both operands are untyped integer expressions.
        # Arithmetic can use the surrounding type context.

        elif left == INT_LITERAL and right == INT_LITERAL:
            if (
                node.op in arithmetic
                and expected is not None
                and expected.is_integer()
            ):
                left = self.analyze_expression(
                    node.left, expected
                )

                right = self.analyze_expression(
                    node.right, expected
                )

        # No implicit conversion between concrete types.

        if left != right:
            raise SemanticError(
                f"Operator {node.op.name} cannot be applied "
                f"to {left} and {right}"
            )

        if left == VOID:
            raise SemanticError(
                "Cannot use void in a binary expression"
            )

        if node.op in arithmetic + comparison:
            if not left.is_integer() and left != INT_LITERAL:
                raise SemanticError(
                    f"Operator {node.op.name} requires integers"
                )

        if node.op in comparison + equality:
            result = BOOL

        else:
            result = left

        # Evaluate constant expressions when possible.

        self.evaluate_binary_constant(node, result)

        return result

    # Unary expressions

    def analyze_unary(
        self,
        node: UnaryExpression,
        expected: DataType | None
    ) -> DataType:

        if node.op == TokenKind.NOT:
            self.analyze_expression(node.operand, BOOL)

            if id(node.operand) in self.constant_values:
                self.constant_values[id(node)] = (
                    not self.constant_values[id(node.operand)]
                )

            return BOOL

        if node.op == TokenKind.MINUS:
            operand_type = self.analyze_expression(node.operand)

            if operand_type == INT_LITERAL:
                value = -self.constant_values[id(node.operand)]

                self.constant_values[id(node)] = value

                if expected is None or expected == INT_LITERAL:
                    return INT_LITERAL

                if not expected.is_integer():
                    raise SemanticError(
                        f"Cannot negate an integer as {expected}"
                    )

                if not expected.fits(value):
                    raise SemanticError(
                        f"Integer {value} does not fit in "
                        f"{expected}"
                    )

                return expected

            if not operand_type.is_integer():
                raise SemanticError(
                    "Arithmetic negation requires an integer"
                )

            if id(node.operand) in self.constant_values:
                value = -self.constant_values[id(node.operand)]

                self.constant_values[id(node)] = cast_value(
                    value,
                    operand_type
                )

            return operand_type

        raise SemanticError(
            f"Unknown unary operator {node.op.name}"
        )

    # Function calls

    def analyze_call(self, node: Call) -> DataType:
        symbol = self.resolve_symbol(node.name)

        if not isinstance(symbol, FunctionSymbol):
            raise SemanticError(
                f"'{node.name}' is not a function"
            )

        if len(node.arguments) != len(symbol.parameters):
            raise SemanticError(
                f"Function '{node.name}' expects "
                f"{len(symbol.parameters)} arguments, got "
                f"{len(node.arguments)}"
            )

        for argument, parameter in zip(
            node.arguments,
            symbol.parameters
        ):
            self.analyze_expression(
                argument,
                parameter.type
            )

        self.resolved_symbols[id(node)] = symbol

        return symbol.return_type

    # Explicit casting

    def analyze_cast(self, node: Cast) -> DataType:
        source = self.analyze_expression(node.value)
        destination = self.resolve_type(node.type)

        if not can_cast(source, destination):
            raise SemanticError(
                f"Cannot cast {source} to {destination}"
            )

        if id(node.value) in self.constant_values:
            value = self.constant_values[id(node.value)]

            self.constant_values[id(node)] = cast_value(
                value,
                destination
            )

        return destination

    # Constant evaluation

    def evaluate_binary_constant(
        self,
        node: BinaryExpression,
        result_type: DataType
    ) -> None:

        # Remove any previous result if this expression
        # is being analyzed again with a different context.

        self.constant_values.pop(id(node), None)

        if (
            node.op in (TokenKind.SLASH, TokenKind.PERCENT)
            and id(node.right) in self.constant_values
            and self.constant_values[id(node.right)] == 0
        ):
            raise SemanticError("Division by zero")

        if (
            id(node.left) not in self.constant_values
            or id(node.right) not in self.constant_values
        ):
            return

        left = self.constant_values[id(node.left)]
        right = self.constant_values[id(node.right)]

        match node.op:
            case TokenKind.PLUS:
                value = left + right

            case TokenKind.MINUS:
                value = left - right

            case TokenKind.STAR:
                value = left * right

            case TokenKind.SLASH:
                value = self.integer_divide(left, right)

            case TokenKind.PERCENT:
                quotient = self.integer_divide(left, right)
                value = left - quotient * right

            case TokenKind.EQ:
                value = left == right

            case TokenKind.NEQ:
                value = left != right

            case TokenKind.LT:
                value = left < right

            case TokenKind.GT:
                value = left > right

            case TokenKind.LTE:
                value = left <= right

            case TokenKind.GTE:
                value = left >= right

            case _:
                return

        if result_type.is_integer():
            value = cast_value(value, result_type)

        self.constant_values[id(node)] = value

    def integer_divide(self, left: int, right: int) -> int:
        if right == 0:
            raise SemanticError("Division by zero")

        quotient = abs(left) // abs(right)

        if (left < 0) != (right < 0):
            quotient = -quotient

        return quotient

    # Control flow analysis

    def block_returns(self, node: Block) -> bool:
        for statement in node.statements:
            if self.statement_returns(statement):
                return True

        return False

    def statement_returns(self, node: Statement) -> bool:
        match node:
            case Return():
                return True

            case If():
                if node.else_body is None:
                    return False

                if not self.block_returns(node.body):
                    return False

                if isinstance(node.else_body, Block):
                    return self.block_returns(node.else_body)

                if isinstance(node.else_body, If):
                    return self.statement_returns(node.else_body)

                return False

            case _:
                return False


class SemanticError(Exception):
    pass
