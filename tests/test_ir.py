from ir import *
from typesys import resolve_type


u32 = resolve_type("u32")

module = IRModule()

function = IRFunction(
    "main",
    [],
    u32
)

entry = BasicBlock(Label("entry"))

address = Address(0, u32)
temp0 = Temporary(0, u32)
temp1 = Temporary(1, u32)

entry.append(
    Instruction(
        Opcode.ALLOC,
        result=address
    )
)

entry.append(
    Instruction(
        Opcode.STORE,
        [Constant(5, u32), address]
    )
)

entry.append(
    Instruction(
        Opcode.LOAD,
        [address],
        temp0
    )
)

entry.append(
    Instruction(
        Opcode.ADD,
        [temp0, Constant(3, u32)],
        temp1
    )
)

entry.append(
    Instruction(
        Opcode.RET,
        [temp1]
    )
)

function.append(entry)
module.append(function)

print(module)
