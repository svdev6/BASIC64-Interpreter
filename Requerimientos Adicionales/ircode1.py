from typing import Any, List, Dict
from basast import *
from baslex import Lexer
from basparse import Parser

# Visitor base class
class Visitor:
    def visit(self, node: Any, *args, **kwargs):
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node: Any, *args, **kwargs):
        raise Exception(f'No visit_{node.__class__.__name__} method')

# IR Code Generator
class IRCodeGenerator(Visitor):
    def __init__(self):
        self.code = []
        self.label_count = 0

    def generate(self, program: 'Program') -> List[tuple]:
        self.code = []
        self.visit(program)
        return self.code

    def emit(self, instruction: str, *args: Any):
        self.code.append((instruction, *args))

    def new_label(self) -> str:
        label = f'L{self.label_count}'
        self.label_count += 1
        return label
    
    def visit_list(self, nodes: List[Any]):
        for node in nodes:
            self.visit(node)
    
    def visit_NoneType(self, node):
        pass

    def visit(self, node, *args, **kwargs):
        print(f"Visiting node: {node}")
        return super().visit(node, *args, **kwargs)

    def visit_Program(self, node: 'Program'):
        for line_number, statement in sorted(node.lines.items()):
            self.visit(statement)

    def visit_Read(self, node: 'Read'):
        for var in node.varlist:
            self.emit('READ', var.var)

    def visit_Let(self, node: 'Let'):
        self.visit(node.expr)
        self.emit('LOCAL_SET', node.var.var)

    def visit_Print(self, node: 'Print'):
        self.visit_list(node.plist)
        self.emit('PRINTI')  # Assume all prints are integers for simplicity
        if node.optend:
            self.emit('PRINTB', ord(node.optend))

    def visit_Input(self, node: 'Input'):
        for var in node.vlist:
            self.emit('INPUT', var.var)

    def visit_For(self, node: 'For'):
        start_label = self.new_label()
        end_label = self.new_label()
        self.visit(node.low)
        self.emit('LOCAL_SET', node.ident.var)
        self.emit(f'{start_label}:')
        self.visit(node.top)
        self.emit('LOCAL_GET', node.ident.var)
        self.emit('GTI')
        self.emit('CBREAK', end_label)
        self.visit(node.step)
        self.emit('LOCAL_GET', node.ident.var)
        self.emit('ADDI')
        self.emit('LOCAL_SET', node.ident.var)
        self.emit('CONTINUE', start_label)
        self.emit(f'{end_label}:')

    def visit_Next(self, node: 'Next'):
        pass  # Handled in visit_For

    def visit_Remark(self, node: 'Remark'):
        pass  # No IR code for remarks

    def visit_End(self, node: 'End'):
        self.emit('END')

    def visit_Stop(self, node: 'Stop'):
        self.emit('STOP')

    def visit_Unary(self, node: 'Unary'):
        self.visit(node.expr)
        if node.op == '-':
            self.emit('CONSTI', 0)
            self.emit('SUBI')
        elif node.op == '+':
            pass  # No operation needed for unary plus

    def visit_Binary(self, node: 'Binary'):
        self.visit(node.left)
        self.visit(node.right)
        if node.op == '+':
            self.emit('ADDI')
        elif node.op == '-':
            self.emit('SUBI')
        elif node.op == '*':
            self.emit('MULI')
        elif node.op == '/':
            self.emit('DIVI')
    
    def visit_Number(self, node: 'Number'):
        self.emit('CONSTI', node.value)

    def visit_String(self, node: 'String'):
        for char in node.value:
            self.emit('CONSTI', ord(char))
            self.emit('PRINTB')

    def visit_Variable(self, node: 'Variable'):
        self.emit('LOCAL_GET', node.var)

    def visit_Literal(self, node: 'Literal'):
        if isinstance(node, Number):
            self.emit('CONSTI', node.value)
        elif isinstance(node, String):
            for char in node.value:
                self.emit('CONSTI', ord(char))
                self.emit('PRINTB')

    def visit_IfStatement(self, node: 'IfStatement'):
        self.visit(node.relexpr)
        end_label = self.new_label()
        self.emit('IF')
        self.emit('JMP', end_label)
        self.emit(f'{end_label}:')

    def visit_Goto(self, node: 'Goto'):
        self.emit('JMP', node.lineno)

    def visit_Data(self, node: 'Data'):
        pass  # Data handling not implemented

    def visit_Restore(self, node: 'Restore'):
        pass  # Restore handling not implemented

    def visit_GoSub(self, node: 'GoSub'):
        self.emit('CALL', node.lineno)

    def visit_Dim(self, node: 'Dim'):
        for var in node.dimlist:
            self.emit('DIM', var.var)

    def visit_Def(self, node: 'Def'):
        pass  # Function definition handling not implemented

    def visit_Call(self, node: 'Call'):
        self.emit('CALL', node.name)

    def visit_Return(self, node: 'Return'):
        self.emit('RET')

    def visit_Group(self, node: 'Group'):
        self.visit(node.expr)
    

# Example usage
if __name__ == "__main__":
    # Assuming parser is available and returns a Program node
    import sys
    l = Lexer()
    p = Parser()

    if len(sys.argv) != 2:
        print("Uso: python basircode.py <archivo.bas>")
        sys.exit(1)

    source_file = sys.argv[1]
    with open(source_file, 'r') as file:
        source_code = file.read()

    tokens = l.tokenize(source_code)
    ast = p.parse(tokens)
    
    ir_generator = IRCodeGenerator()
    ir_code = ir_generator.generate(ast)
    for instr in ir_code:
        print(instr)