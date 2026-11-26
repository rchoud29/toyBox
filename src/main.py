import argparse, subprocess, sys, tempfile
from pathlib import Path
from pprint import pprint
from lexer import Lexer, LexerError
from parser import Parser, ParserError
from semantic import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from ir import IRError
from backend import Backend, BackendError


def main():
    p = argparse.ArgumentParser(description='toyBox compiler')
    p.add_argument('source', type=Path)
    p.add_argument('-o', '--output', type=Path, default=Path('a.out'))
    for flag in ('tokens', 'ast', 'ir', 'asm'):
        p.add_argument('--emit-' + flag, action='store_true')
    p.add_argument('--keep-files', action='store_true')
    args = p.parse_args()
    try:
        tokens = Lexer(args.source.read_text(encoding='utf-8')).tokenize()
        if args.emit_tokens:
            pprint(tokens)
            return
        ast = Parser(tokens).parse_program()
        if args.emit_ast:
            pprint(ast)
            return
        sem = SemanticAnalyzer()
        sem.analyze(ast)
        module = IRGenerator(sem).generate(ast)
        if args.emit_ir:
            print(module)
            return
        asm = Backend().generate(module)
        if args.emit_asm:
            print(asm, end='')
            return
        out = args.output.resolve()
        if out == args.source.resolve():
            raise BackendError('Output would overwrite source')
        with tempfile.TemporaryDirectory() as tmp:
            af = Path(tmp) / 'output.asm'
            of = Path(tmp) / 'output.o'
            af.write_text(asm)
            subprocess.run(['nasm',
                '-f',
                'elf64',
                str(af),
                '-o',
                str(of)],
                check=True)
            subprocess.run(['ld', str(of), '-o', str(out)], check=True)
            if args.keep_files:
                for f, suffix in ((af, '.asm'), (of, '.o')):
                    dest = Path(str(out) + suffix)
                    if dest.resolve() == args.source.resolve():
                        raise BackendError('Intermediate overwrites source')
                    dest.write_bytes(f.read_bytes())
        print(f'Compiled: {out}')
    except (LexerError,
        ParserError,
        SemanticError,
        IRError,
        BackendError,
        OSError,
        subprocess.CalledProcessError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
