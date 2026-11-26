# toyBox

**toyBox** is an experimental, statically typed programming language and native compiler implemented in Python. The current compiler translates toyBox source into NASM x86-64 assembly, assembles it with NASM, and links a Linux executable with GNU `ld`.

This README documents the **current implementation**, not proposed language features.

## Requirements

- Python 3.10 or newer (the compiler uses structural pattern matching and modern type annotations)
- Linux x86-64 for the generated executable
- `nasm` and GNU `ld` available on `PATH`

All compiler Python modules are expected to be in the same directory. No third-party Python packages are imported by the supplied implementation.

On Debian/Ubuntu, the native toolchain can be installed with:

```bash
sudo apt update
sudo apt install nasm binutils
```

## Quick start

Save this example as `example.tb`:

```text
fn add(a: u32, b: u32): u32 {
    return a + b;
}

fn main(): u32 {
    df result: u32 = add(1, 2);
    return result;
}
```

Compile and run it:

```bash
python3 main.py example.tb -o example
./example
echo $?
```

The executable returns `3` as its process exit status. **There is no built-in print/console function in the supplied code.** A non-void `main` returns its integer result as the Linux process exit status; a `void` main exits with status zero.

## Command-line interface

```text
python3 main.py SOURCE [-o OUTPUT] [--emit-tokens] [--emit-ast]
                       [--emit-ir] [--emit-asm] [--keep-files]
```

| Option | Behavior |
| --- | --- |
| `SOURCE` | Path to the toyBox source file (required). |
| `-o`, `--output` | Executable path; defaults to `a.out`. |
| `--emit-tokens` | Print the lexer output and stop. |
| `--emit-ast` | Print the parsed AST and stop. |
| `--emit-ir` | Print the generated intermediate representation and stop. |
| `--emit-asm` | Print the generated NASM assembly and stop. |
| `--keep-files` | Preserve the `.asm` and `.o` files alongside the executable. |

Examples:

```bash
python3 main.py example.tb --emit-tokens
python3 main.py example.tb --emit-ast
python3 main.py example.tb --emit-ir
python3 main.py example.tb --emit-asm
python3 main.py example.tb -o build/example --keep-files
```

When producing an executable, the compiler writes `OUTPUT.asm`, assembles it to `OUTPUT.o` using `nasm -f elf64`, and links `OUTPUT` using `ld`. It removes the intermediate files unless `--keep-files` is supplied. Create any desired output directory beforehand.

## Language reference

### Functions

```text
fn multiply(a: i32, b: i32): i32 {
    return a * b;
}

fn main(): i32 {
    return multiply(6, 7);
}
```

Functions have explicit parameter types and an explicit return type. Calls can appear as expressions or as standalone statements. Function signatures are registered before bodies are checked, allowing calls to functions declared later in the file.

The native entry point requires a function named `main` with no parameters and a `void` or integer return type. Function and variable name resolution is case-insensitive.

### Types

| Syntax | Meaning |
| --- | --- |
| `uN` | Unsigned integer with N bits. |
| `iN` | Signed integer with N bits. |
| `bool` | Boolean. |
| `void` | No value; valid as a function return type. |

The type resolver accepts positive integer widths expressed as `uN`/`iN`, but the **native backend supports widths 1 through 64 only**. Integer literals initially have an internal `integer literal` type and are resolved using context. Literal values are checked against the destination type's range. Concrete types do not implicitly convert; use an explicit cast.

### Variables and assignment

```text
fn main(): u32 {
    df count: u32 = 2;
    st count = count + 3;
    return count;
}
```

`df` declares and initializes a variable. `st` assigns a new value to an existing variable. Variables must be declared before use and cannot have type `void`. Nested blocks introduce scopes, and the symbol table rejects duplicate definitions within the same scope.

### Expressions and operators

| Category | Operators |
| --- | --- |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Comparisons | `<`, `>`, `<=`, `>=` |
| Equality | `==`, `!=` |
| Unary | `-`, `!` |
| Grouping | `(expression)` |
| Explicit cast | `expression: type` |

Multiplication, division, and remainder bind more tightly than addition/subtraction; comparisons follow arithmetic; equality follows comparisons. Unary operators bind more tightly than binary operators. A postfix type annotation performs a cast, for example `(value + 1): i64`.

Comparisons produce `bool`. `if` and `while` conditions must be `bool`. Arithmetic operands must have compatible integer types. The semantic analyzer evaluates constant expressions when possible and rejects known division by zero; the native backend also emits a trap for runtime division by zero.

### Conditionals

```text
fn max(a: i32, b: i32): i32 {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}
```

`if`, `else`, and `else if` are supported. Both branches must return for an `if` statement to establish a guaranteed return path.

### Loops

```text
fn sum_to(n: u32): u32 {
    df i: u32 = 0;
    df total: u32 = 0;
    while (i < n) {
        st total = total + i;
        st i = i + 1;
    }
    return total;
}
```

The current parser supports `while` loops. It does not implement `for`, `break`, or `continue`.

### Simplified grammar

```ebnf
program       = { function } , EOF ;
function      = "fn" , identifier , "(" , [ parameters ] , ")" , ":" , type , block ;
parameters    = parameter , { "," , parameter } ;
parameter     = identifier , ":" , type ;
block         = "{" , { statement } , "}" ;
statement     = declaration | assignment | return_stmt | if_stmt | while_stmt | call , ";" ;
declaration   = "df" , identifier , ":" , type , "=" , expression , ";" ;
assignment    = "st" , identifier , "=" , expression , ";" ;
return_stmt   = "return" , [ expression ] , ";" ;
if_stmt       = "if" , "(" , expression , ")" , block , [ "else" , ( block | if_stmt ) ] ;
while_stmt    = "while" , "(" , expression , ")" , block ;
expression    = equality ;
equality      = comparison , { ( "==" | "!=" ) , comparison } ;
comparison    = additive , { ( "<" | ">" | "<=" | ">=" ) , additive } ;
additive      = multiplicative , { ( "+" | "-" ) , multiplicative } ;
multiplicative = unary , { ( "*" | "/" | "%" ) , unary } ;
unary         = ( "-" | "!" ) , unary | postfix ;
postfix       = primary , { ":" , type } ;
primary       = integer | boolean | identifier , [ "(" , [ arguments ] , ")" ]
              | "(" , expression , ")" ;
call          = identifier , "(" , [ arguments ] , ")" ;
arguments     = expression , { "," , expression } ;
type          = identifier ;
```

Identifiers start with an ASCII letter or underscore and may continue with ASCII letters, digits, or underscores. Keywords and Boolean literals are recognized case-insensitively. The lexer recognizes whitespace but has no comment-handling rule in the supplied implementation.

## Compiler architecture

```text
Source
  -> Lexer -> Tokens
  -> Parser -> AST
  -> Semantic analyzer (types + scoped symbols + constants)
  -> IR generator -> Typed, basic-block IR
  -> Backend -> NASM x86-64 assembly
  -> NASM -> ELF64 object
  -> GNU ld -> Linux executable
```

| File | Responsibility |
| --- | --- |
| `main.py` | CLI, compiler orchestration, NASM/ld invocation, diagnostics. |
| `tokens.py` | Token kinds, keyword/operator/delimiter mappings, token location metadata. |
| `lexer.py` | Scans source into tokens and reports unexpected characters. |
| `parser.py` | Recursive-descent parser with precedence-aware expressions. |
| `ast_nodes.py` | Dataclass-based program, statement, and expression nodes. |
| `typesys.py` | Integer/Boolean/void types, integer ranges, explicit cast rules. |
| `symbols.py` | Variable/function symbols and nested lexical scopes. |
| `semantic.py` | Name resolution, type checking, return-path checks, constant evaluation. |
| `ir.py` | Typed IR operands, opcodes, instructions, basic blocks, functions, modules. |
| `ir_generator.py` | AST-to-IR lowering, local allocations, calls, branches, loops. |
| `backend.py` | IR-to-NASM translation, stack layout, calling convention, Linux entry point. |

### Lexer and parser

`Lexer.tokenize()` scans the source and emits `Token(kind, lexeme, line, column)` records, ending with an `EOF` token. Multi-character operators are recognized using longest-match lookup. Invalid characters raise `LexerError` with a source-line pointer.

`Parser.parse_program()` consumes the token stream and constructs an AST. It uses separate methods for each grammar production and operator-precedence level. Unexpected tokens raise `ParserError` with token position and lexeme information.

### Semantic analysis

`SemanticAnalyzer.analyze()` performs two passes:

1. Register all function signatures in the global scope.
2. Analyze function bodies with nested scopes, resolving identifiers and checking types.

It records information for subsequent compilation stages in dictionaries indexed by `id(ast_node)`:

- `expression_types`: resolved type of each expression.
- `resolved_symbols`: the symbol associated with identifiers, calls, declarations, and functions.
- `constant_values`: compile-time evaluated literal expressions.

It validates function arguments, declaration and assignment types, Boolean conditions, explicit casts, and non-void return paths. There are no implicit conversions between different concrete types.

### Intermediate representation

`ir.py` defines an explicit typed IR with these operand forms:

- `Constant`: typed immediate value.
- `Temporary`: result of an intermediate computation.
- `Address`: storage location for a local variable.
- `IRParameter`: incoming function parameter.
- `Label`: basic-block destination.
- `FunctionRef`: target of a function call.

IR opcodes include `alloc`, `load`, `store`, arithmetic, comparisons, `not`, `cast`, `jmp`, `br`, `call`, and `ret`. Each basic block must terminate in a jump, branch, or return before code generation. `IRGenerator` creates entry blocks, inserts local allocations, and lowers `if` and `while` into explicit control-flow blocks.

### Native backend

The backend emits NASM Intel-syntax assembly for x86-64 Linux. It:

- Reserves stack slots for parameters, locals, and temporaries.
- Normalizes integer results to their declared bit width, including sign extension for signed types.
- Uses System V integer argument registers `rdi`, `rsi`, `rdx`, `rcx`, `r8`, and `r9`; further arguments go on the stack.
- Aligns the stack to 16 bytes at call sites.
- Uses `rax` for integer return values.
- Emits an `_start` entry point that calls `fn_main` and exits via Linux syscall 60.
- Emits `ud2` on a runtime division-by-zero path.

The backend currently uses stack-based storage rather than a register allocator. There is no separate optimization pass; the semantic analyzer does perform constant evaluation.

## Error handling

The pipeline has dedicated exception types: `LexerError`, `ParserError`, `SemanticError`, `IRError`, and `BackendError`. The CLI also handles OS and subprocess errors, prints the error to standard error, and exits with code 1. Lexer diagnostics include a caret pointing to the offending source position; parser diagnostics include the token position.

## Current limitations

The following are **not implemented in the supplied files**:

- String or floating-point literals, arrays, structures, pointers, or manual memory management in the source language.
- Source-level comments.
- Imports, modules, namespaces, standard-library functions, or console output.
- `for` loops, `break`, `continue`, or logical `&&`/`||` operators.
- Generic functions, macros, decorators, or syntactic-sugar expansion.
- Windows/macOS executable targets or non-x86-64 backends.
- A dedicated test suite or optimization pipeline.

Additional constraints: The native backend rejects integer widths greater than 64 even though the type parser accepts their names. `main` must take no parameters. The compiler invokes NASM and `ld` directly and does not link a C runtime.

## Contributing and development

A useful development workflow is to inspect each stage independently:

```bash
python3 main.py example.tb --emit-tokens
python3 main.py example.tb --emit-ast
python3 main.py example.tb --emit-ir
python3 main.py example.tb --emit-asm
```

When adding syntax, update `tokens.py` and `lexer.py` if new tokens are needed; `parser.py` and `ast_nodes.py` for new grammar constructs; `semantic.py`, `typesys.py`, and `symbols.py` for typing and name resolution; `ir.py` and `ir_generator.py` for lowering; and `backend.py` for native execution. Add end-to-end tests for accepted programs, rejected programs, and edge cases before treating a feature as complete.

## Status

Experimental compiler prototype. This documentation reflects the provided source files and does not claim that all language examples or edge cases have been tested on a native Linux toolchain.
