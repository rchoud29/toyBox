from __future__ import annotations
from dataclasses import dataclass
from typesys import DataType


@dataclass
class VariableSymbol:
    name: str
    type: DataType


@dataclass
class FunctionSymbol:
    name: str
    parameters: list[VariableSymbol]
    return_type: DataType


Symbol = VariableSymbol | FunctionSymbol


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        name = symbol.name.lower()

        if name in self.symbols:
            raise SymbolError(
                f"'{symbol.name}' is already defined"
            )

        self.symbols[name] = symbol

    def resolve(self, name: str) -> Symbol:
        key = name.lower()

        if key in self.symbols:
            return self.symbols[key]

        if self.parent is not None:
            return self.parent.resolve(name)

        raise SymbolError(f"Undefined identifier '{name}'")

    def contains(self, name: str) -> bool:
        return name.lower() in self.symbols


class SymbolError(Exception):
    pass
