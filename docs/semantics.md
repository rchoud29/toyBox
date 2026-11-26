# Language semantics

Names are ASCII and case-insensitive. Original spelling is retained in tokens.
Variables and parameters are mutable. Each binding requires an explicit type and initializer. Bindings in a declaration are evaluated and introduced left to right, in the enclosing scope. Duplicate names in a scope are rejected; nested scopes may shadow names. Function signatures are registered before bodies.

Types: bool, void, and uN/iN for positive decimal widths N without leading zeros. Signed integers use two's complement. Void is only a return type. Integer literals are contextual; concrete types never implicitly convert. Constant-only expressions without a concrete context use arbitrary precision. Typed arithmetic wraps; division truncates toward zero, remainder is dividend minus quotient times divisor. Constant division by zero is rejected; runtime division by zero traps. Conditions require bool. Casts use postfix :type, bind tighter than unary operators, and can chain. Integer casts truncate or extend according to source signedness; boolean conversions test nonzero or yield zero/one. Non-void functions require a return on all paths (conservative loop analysis).

Native backend: x86-64 Linux, NASM and GNU ld, integer widths 1 through 64, bool and void. Wider runtime types are rejected; frontend and constant evaluation support wider types. Stack slots are eight bytes, not a source-level layout guarantee. Parameterless integer or void main is required for native output. Exit status exposes only the low eight bits.

## Usage

    sudo apt install nasm binutils
    python3 src/main.py examples/test.tl -o test
    ./test
    echo $?

Use --emit-tokens, --emit-ast, --emit-ir, --emit-asm to inspect individual stages; --keep-files retains assembly and object files. Python 3.10+ required.
