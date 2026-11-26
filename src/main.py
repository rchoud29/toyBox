import argparse
import subprocess
import sys

from pathlib import Path

from lexer import Lexer, LexerError
from parser import Parser, ParserError
from semantic import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from ir import IRError
from backend import Backend, BackendError


def main():
    cli = argparse.ArgumentParser(
        description="toyBox native compiler"
    )

    cli.add_argument(
        "source",
        type=Path,
        help="Source file"
    )

    cli.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("a.out"),
        help="Output executable"
    )

    cli.add_argument(
        "--emit-tokens",
        action="store_true"
    )

    cli.add_argument(
        "--emit-ast",
        action="store_true"
    )

    cli.add_argument(
        "--emit-ir",
        action="store_true"
    )

    cli.add_argument(
        "--emit-asm",
        action="store_true"
    )

    cli.add_argument(
        "--keep-files",
        action="store_true"
    )

    args = cli.parse_args()

    try:
        src = args.source.read_text(
            encoding="utf-8"
        )

        # Lexical analysis

        lexer = Lexer(src)
        tokens = lexer.tokenize()

        if args.emit_tokens:
            for token in tokens:
                print(token)

            return

        # Parsing

        parser = Parser(tokens)
        ast = parser.parse_program()

        if args.emit_ast:
            from pprint import pprint

            pprint(ast)
            return

        # Semantic analysis

        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        # Intermediate representation

        generator = IRGenerator(analyzer)
        module = generator.generate(ast)

        if args.emit_ir:
            print(module)
            return

        # Native code generation

        backend = Backend()
        assembly = backend.generate(module)

        if args.emit_asm:
            print(assembly)
            return

        # Output files

        output = args.output

        asm_file = Path(f"{output}.asm")
        obj_file = Path(f"{output}.o")

        if args.source.resolve() in (
            output.resolve(),
            asm_file.resolve(),
            obj_file.resolve()
        ):
            raise BackendError(
                "Output would overwrite the source file"
            )

        asm_file.write_text(
            assembly,
            encoding="utf-8"
        )

        # Assemble

        subprocess.run(
            [
                "nasm",
                "-f",
                "elf64",
                str(asm_file),
                "-o",
                str(obj_file)
            ],
            check=True
        )

        # Link

        subprocess.run(
            [
                "ld",
                str(obj_file),
                "-o",
                str(output)
            ],
            check=True
        )

        # Clean intermediate files

        if not args.keep_files:
            asm_file.unlink()
            obj_file.unlink()

        print(f"Compiled: {output}")

    except (
        LexerError,
        ParserError,
        SemanticError,
        IRError,
        BackendError,
        OSError,
        subprocess.CalledProcessError
    ) as error:

        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
