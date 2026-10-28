import sys

class ToyLang:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.token_feed = self.tokens()
        self.returned_tokens = []
        self.stack = []
        self.vars = {}

    def raise_error(self, msg):
        raise ValueError(f'{self.pos}: {msg}')

    def push(self, arg):
        return self.stack.append(arg)
    def pop(self):
        return self.stack.pop()

    def collapse(self):
        while len(self.stack) >= 3:
            b = self.pop()
            op = self.pop()
            a = self.pop()

            match op:
                case "+":
                    self.push(a + b)
                case "-":
                    self.push(a - b)
                case "*":
                    self.push(a * b)
                case "/":
                    self.push(a // b)
                case _:
                    self.push(a)
                    self.push(op)
                    self.push(b)

            return self.pop()
        return self.pop()
   


    def islegal(self, char):
        allowed = {'(',')',';','\n',' ','_','<EOF>'}
        return bool(char) and \
                (ispunctuation(char) or isidentifierpart(char) or \
                 char in allowed)

    def ispunctuation(self, char):
        allowed = {'(',')',';','='}
        return  char in allowed

    def isoperator(self, char):
        allowed = {'+', '-', '*', '/'}
        return char in allowed

    def isidentifierstart(self, char):
        allowed = {}
        return char.isalpha() or char in allowed
    def isidentifierpart(self, char):
        allowed = {'_'}
        return char.isalpha() or char in allowed


    def next_token(self):
        if self.returned_tokens:
            token = self.returned_tokens.pop()
        else:
            try:
                token = next(self.token_feed)
            except StopIteration:
                token = None

        return token
    
    def return_token(self, token):
        if token is not None:
            self.returned_tokens.append(token)

    def return_tokens(self, tokens):
        for token in tokens:
            return_token(token)



    def tokens(self):
        while self.pos < len(self.code):
            char = self.code[self.pos]
            start = self.pos

            if char.isspace():
                self.pos += 1
                continue

            if self.ispunctuation(char):
                yield ('punctuation', char)
                self.pos += 1
                continue
            
            if self.isoperator(char):
                yield ('operator', char)
                self.pos += 1
                continue

            if self.isidentifierstart(char):
                while self.pos < len(self.code) and \
                        self.isidentifierpart(self.code[self.pos]):
                    self.pos += 1
                yield ('identifier', self.code[start:self.pos])
                continue

            if char.isdigit():
                while self.pos < len(self.code) and \
                                 self.code[self.pos].isdigit():
                    self.pos += 1
                yield ('number', int(self.code[start:self.pos]))
                continue
            
            self.raise_error(f"Unexpected character '{char}'")



    def parse_value(self):
        token = self.next_token()
        if token[0] not in {"number", "identifier"}:
            self.return_token(token)
            return False

        if token[0] == 'number':
            self.push(token[1])
            return True
        if token[0] == 'identifier':
            if token[1] not in self.vars:
                self.raise_error(f"Syntax Error: Unkown variable {token[1]}")
            else:
                self.push(self.vars[token[1]])
            return True

        self.raise_error(f"idk how i got here")

    def parse_operator(self):
        token = self.next_token()
        if token[0] != "operator":
            self.return_token(token)
            return False
        
        self.push(self.collapse())
        self.push(token[1])
        return True

    def parse_expression(self):
        if not self.parse_value():
            return False
        if self.parse_operator():
            self.parse_expression()

        return True

    def parse_print_statement(self):
        token = self.next_token()
        if token[1] != 'print':
            self.return_token(token)
            return False

        token = self.next_token()
        if token[1] != '(':
            self.raise_error("Expected: '('")
            return False

        if not self.parse_expression():
            self.raise_error('Expected: expression')

        token = self.next_token()
        if token[1] != ')':
            self.raise_error("Expected: ')'")

        print(self.collapse())
        return True

    def parse_assignment(self):
        token = self.next_token()
        if token[0] != 'identifier':
            self.return_token(token)
            return False
        identifier = token[1]

        token = self.next_token()
        if token[1] != '=':
            self.raise_error("Expected: '='")
        if not self.parse_expression():
            self.raise_error("Expected: expression")

        self.vars[identifier] = self.collapse()
        return True


    def parse_statement(self):
        if not self.parse_print_statement() and \
           not self.parse_assignment():
            self.raise_error('Expected: legal statement')
        token = self.next_token();
        if token[1] != ';':
            self.raise_error('Expected: statement terminator (\';\')')
        return True

    def parse_program(self):
        if not self.parse_statement():
            self.raise_error('Expected: statement')

        token = self.next_token()
        while token is not None:
            self.return_token(token)
            if not self.parse_statement():
                self.raise_error('Expected: statement')
            token = self.next_token()

        return True


    
    def run(self):
        try:
            return self.parse_program()
        except ValueError as exc:
            print(str(exc))
            return False

if __name__ == '__main__':
    with open(sys.argv[1], 'rt') as f:
        code = f.read()
    program = ToyLang(code)
    program.run()
