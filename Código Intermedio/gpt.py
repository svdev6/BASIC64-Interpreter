from basast import *

class IRGenerator(Visitor):
    def __init__(self):
        self.code = []

    def generate(self, node):
        self.visit(node)
        return self.code

    def visit_Program(self, node):
        for line_number, stmt in node.lines.items():
            stmt.accept(self)

    def visit_Let(self, node):
        node.expr.accept(self)
        self.code.append(('LOCAL_SET', node.var.var))

    def visit_Print(self, node):
        for item in node.plist:
            if isinstance(item, Expression):
                item.accept(self)
                self.code.append(('PRINTI',))
            elif isinstance(item, str):
                for char in item:
                    self.code.append(('CONSTI', ord(char)))
                    self.code.append(('PRINTB',))
        if node.optend is not None:
            if node.optend == ',':
                pass  # Do nothing
            elif node.optend == ';':
                self.code.append(('CONSTI', ord('\t')))
                self.code.append(('PRINTB',))
            else:
                self.code.append(('CONSTI', ord('\n')))
                self.code.append(('PRINTB',))

    def visit_Input(self, node):
        # Assuming input handling outside of IR scope for simplicity
        pass

    def visit_IfStatement(self, node):
        node.relexpr.accept(self)
        self.code.append(('IF',))
        # Jump address to be filled later
        self.code.append(('JUMP', None))
        node.lineno.accept(self)

    def visit_Goto(self, node):
        self.code.append(('JUMP', node.lineno))

    def visit_For(self, node):
        node.low.accept(self)
        self.code.append(('LOCAL_SET', node.ident.var))
        self.code.append(('LABEL', node.ident.var))
        node.top.accept(self)
        self.code.append(('LOCAL_GET', node.ident.var))
        self.code.append(('GTI',))
        self.code.append(('IF',))
        self.code.append(('JUMP', None))
        if node.step is not None:
            node.step.accept(self)
        else:
            self.code.append(('CONSTI', 1))
        self.code.append(('LOCAL_GET', node.ident.var))
        self.code.append(('ADDI',))
        self.code.append(('LOCAL_SET', node.ident.var))
        self.code.append(('JUMP', node.ident.var))
        self.code.append(('LABEL', None))

    def visit_Next(self, node):
        self.code.append(('JUMP', node.ident.var))

    def visit_End(self, node):
        self.code.append(('RET',))

    def visit_Stop(self, node):
        self.code.append(('RET',))

    def visit_Return(self, node):
        self.code.append(('RET',))

    def visit_Binary(self, node):
        node.left.accept(self)
        node.right.accept(self)
        if node.op == '+':
            self.code.append(('ADDI',))
        elif node.op == '-':
            self.code.append(('SUBI',))
        elif node.op == '*':
            self.code.append(('MULI',))
        elif node.op == '/':
            self.code.append(('DIVI',))
        elif node.op == '<':
            self.code.append(('LTI',))
        elif node.op == '<=':
            self.code.append(('LEI',))
        elif node.op == '>':
            self.code.append(('GTI',))
        elif node.op == '>=':
            self.code.append(('GEI',))
        elif node.op == '==':
            self.code.append(('EQI',))
        elif node.op == '!=':
            self.code.append(('NEI',))

    def visit_Unary(self, node):
        node.expr.accept(self)
        if node.op == '-':
            self.code.append(('CONSTI', 0))
            self.code.append(('SWAP',))
            self.code.append(('SUBI',))

    def visit_Variable(self, node):
        self.code.append(('LOCAL_GET', node.var))

    def visit_Number(self, node):
        self.code.append(('CONSTI', node.value))

    def visit_String(self, node):
        for char in node.value:
            self.code.append(('CONSTI', ord(char)))
            self.code.append(('PRINTB',))

    def visit_Call(self, node):
        if node.expr:
            for expr in node.expr:
                expr.accept(self)
        self.code.append(('CALL', node.name))

    def visit_Def(self, node):
        self.code.append(('DEF', node.fn, node.ident, node.expr))

    def visit_Remark(self, node):
        # Comments are ignored in the IR
        pass

# Example usage
if __name__ == '__main__':
    import sys
    from basparse import Parser

    if len(sys.argv) != 2:
        print("Usage: python irgen.py <archivo.bas>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
            parser = Parser()
            program = parser.parse(source_code)

            ir_generator = IRGenerator()
            code = ir_generator.generate(program)
            for instr in code:
                print(instr)

    except FileNotFoundError:
        print(f"El archivo '{file_path}' no se encontró.")
    except Exception as e:
        print(f"Se produjo un error durante la ejecución del programa: {e}")