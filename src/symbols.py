from dataclasses import dataclass
from typesys import DataType


@dataclass(eq=False)

class VariableSymbol:
    name: str
    type: DataType


@dataclass(eq=False)

class FunctionSymbol:
    name: str
    parameters: list[VariableSymbol]
    return_type: DataType
Symbol = VariableSymbol | FunctionSymbol


class SymbolError(Exception):
    pass


class Scope:

    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def define(self, s):
        k = s.name.lower()
        if k in self.symbols:
            raise SymbolError(f'Duplicate declaration {s.name}')
        self.symbols[k] = s

    def resolve(self, name):
        k = name.lower()
        if k in self.symbols:
            return self.symbols[k]
        if self.parent:
            return self.parent.resolve(name)
        raise SymbolError(f'Undefined identifier {name}')

    def contains(self, name):
        return name.lower() in self.symbols
