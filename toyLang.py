import sys
import argparse
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

class ToyLang:
    def __init__(self, code):
        self.code = code
        self.lexer = Lexer(self.code)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter()
        self.ast = None
    
    def run(self):
        try:
            self.ast = self.parser.parse_program()
            return self.interpreter.interpret(self.ast)
        except ValueError as exc:
            print(str(exc))
            return False

    def step(self):
        try:
            self.ast = self.parser.step_program()
        except ValueError as exc:
            print(str(exc))
            return False


if __name__ == '__main__':
    argParser = argparse.ArgumentParser('ToyLang')
    argParser.add_argument('filename')
    argParser.add_argument('-s', '--step', action='store_const', const=1)

    args = argParser.parse_args()
    with open(args.filename, 'rt') as f:
        code = f.read()

    program = ToyLang(code)
    if args.step == 1:
        program.step()
    else:
        program.run()
