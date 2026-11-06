import sys
import argparse
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

class ToyLang:
    def __init__(self, code):
        self.code = code
        self.lexer = None
        self.parser = None
        self.interpreter = Interpreter()
        self.ast = None
    
    def run(self):
        try:
            self.lexer = Lexer(self.code)
            self.parser = Parser(self.lexer)
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

    def tokens(self):
        self.lexer = Lexer(code)
        while self.lexer.peek():
            print(next(self.lexer.tokens()))

    def nodes(self):
        self.lexer = Lexer(self.code)
        self.parser = Parser(self.lexer)
        print(self.parser.parse_program())
        return self.parser.parse_program()



if __name__ == '__main__':
    argParser = argparse.ArgumentParser('ToyLang')
    argParser.add_argument('filename')
    argParser.add_argument('-s', '--step', action='store_const', const=True)
    argParser.add_argument('-t', '--tokens', action='store_const', const=True)
    argParser.add_argument('-n', '--nodes', action='store_const', const=True)
    argParser.add_argument('-r', '--norun', action='store_const', const=True)

    args = argParser.parse_args()
    with open(args.filename, 'rt') as f:
        code = f.read()

    if args.tokens:
        program = ToyLang(code)
        program.tokens()
    if args.nodes:
        program = ToyLang(code)
        program.nodes()
    if args.step:
        program = ToyLang(code)
        program.step()
    if not args.norun:
        program = ToyLang(code)
        program.run()
