# Intermediate representation

Typed three-address instructions, single-assignment temporaries and mutable
local storage. Constants are written `42:u32`, temporaries `%0`, addresses
`$0`, parameters `%arg.x`, function references `@add`, and labels by name. Each
basic block ends in `jmp`, `br` or `ret`. Allocations are hoisted to entry;
initialization stays at the declaration site.

    $0:u32 = alloc
    store 42:u32, $0
    %0:u32 = load $0
    %1:u32 = add %0, 1:u32
    %2:bool = gt %1, 10:u32
    br %2, yes, no

Arithmetic: add, sub, mul, div, mod, neg. Logical: not. Comparisons: eq, neq,
lt, lte, gt, gte. Conversion: cast (destination type is the result type).
Control flow: jmp label, br condition,true,false. Functions: call @name,args;
ret value (or no value for void). Arithmetic and casts follow source semantics.
No full IR verifier or optimizer yet; constant expressions are folded during
lowering.
