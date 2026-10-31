import sys
from lexer import Lexer
from parser import Parser

class ToyLang:
    def __init__(self, code):
        self.code = code
        self.lexer = Lexer(self.code)
        self.parser = Parser(self.lexer)
    
    def run(self):
        try:
            print(self.parser.parse_program())
        except ValueError as exc:
            print(str(exc))
            return False

if __name__ == '__main__':
    with open(sys.argv[1], 'rt') as f:
        code = f.read()
    program = ToyLang(code)
    program.run()
