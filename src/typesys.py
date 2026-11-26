from dataclasses import dataclass
from enum import Enum, auto


class TypeKind(Enum):
    INT = auto()
    BOOL = auto()
    VOID = auto()
    INT_LITERAL = auto()


@dataclass(frozen=True)
class DataType:
    kind: TypeKind
    width: int = 0
    signed: bool = False

    @property
    def name(self) -> str:
        if self.kind == TypeKind.INT:
            prefix = "i" if self.signed else "u"
            return f"{prefix}{self.width}"

        if self.kind == TypeKind.BOOL:
            return "bool"

        if self.kind == TypeKind.VOID:
            return "void"

        return "integer literal"

    @property
    def size(self) -> int:
        return (self.width + 7) // 8

    @property
    def minimum(self) -> int:
        if self.kind != TypeKind.INT:
            raise TypeError("Expected integer type")

        if self.signed:
            return -(1 << (self.width - 1))

        return 0

    @property
    def maximum(self) -> int:
        if self.kind != TypeKind.INT:
            raise TypeError("Expected integer type")

        if self.signed:
            return (1 << (self.width - 1)) - 1

        return (1 << self.width) - 1

    def fits(self, value: int) -> bool:
        return self.minimum <= value <= self.maximum

    def is_integer(self) -> bool:
        return self.kind == TypeKind.INT

    def __str__(self) -> str:
        return self.name


BOOL = DataType(TypeKind.BOOL, 1)
VOID = DataType(TypeKind.VOID)
INT_LITERAL = DataType(TypeKind.INT_LITERAL)


def resolve_type(name: str) -> DataType:
    name = name.lower()

    if name == "bool":
        return BOOL

    if name == "void":
        return VOID

    if (
        len(name) > 1
        and name[0] in ("u", "i")
        and name[1:].isascii()
        and name[1:].isdigit()
        and name[1] != "0"
    ):
        width = int(name[1:])

        return DataType(
            TypeKind.INT,
            width,
            name[0] == "i"
        )

    raise TypeError(f"Unknown type '{name}'")


def can_cast(src: DataType, dest: DataType) -> bool:
    return (
        src.kind != TypeKind.VOID
        and dest.kind in (TypeKind.INT, TypeKind.BOOL)
    )


def cast_value(value: int | bool, dest: DataType) -> int | bool:
    if dest.kind == TypeKind.BOOL:
        return bool(value)

    if dest.kind != TypeKind.INT:
        raise TypeError(f"Cannot cast to {dest}")

    value = int(value)

    # Discard bits outside the destination width.
    mask = (1 << dest.width) - 1
    value &= mask

    # Interpret the remaining bits as two's complement.
    if dest.signed:
        sign_bit = 1 << (dest.width - 1)

        if value & sign_bit:
            value -= 1 << dest.width

    return value
