from baslex import Lexer
from basparse import Parser
from typing import Any, List, Dict
from basast import *
from basinterpir import Interpreter

class IR_Visitor:
    def __init__(self):
        self.code = []
        self.loop_stack = []
        self.step_stack = []
        self.data_stack = []
        self.data_index = 0

    def visit(self, node, *args, **kwargs):
        method = 'visit_' + type(node).__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, *args, **kwargs)
    
    def generic_visit(self, node, *args, **kwargs):
        raise Exception("No visit_{} method".format(type(node).__name__))

    def visit_NoneType(self, node):
        pass
    
    def visit_Program(self, node: Program):
        for line in sorted(node.lines.keys()):
            self.visit(node.lines[line])
        
    def visit_Let(self, node: Let):
        self.visit(node.expr)
        varname = node.var
        self.code.append(('LOCAL_SET', varname.var))

    def visit_Read(self, node: Read):
        pass

    def visit_Data(self, node: Data):
        pass

    def visit_Group(self, node: Group):
        self.visit(node.expr)

    def visit_IfStatement(self, node: IfStatement):
        self.visit(node.relexpr)
        self.code.append(('IF', ))
        self.code.append(('JUMP', node.lineno))
        self.code.append(('ENDIF', ))
    
    def visit_Print(self, node: Print):
        for expr in node.plist:
            if isinstance(expr, String):
                self.visit_String(expr)  # Visit the String node directly
                self.code.append(('PRINTB', ))
            elif isinstance(expr, str):
                for char in expr:
                    self.code.append(('CONSTI', ord(char)))
                    self.code.append(('PRINTB', ))
            else:
                self.visit(expr)
                self.code.append(('PRINTI', ))

    def visit_list(self, nodes: List[Any]):
        for node in nodes:
            self.visit(node)

    def visit_String(self, node: String):
        for char in node.value:
            self.code.append(('CONSTI', ord(char)))
            self.code.append(('PRINTB', ))

    def visit_Input(self, node: Input):
        pass

    def visit_Goto(self, node: Goto):
        self.code.append(('JUMP', node.lineno))
        

    def visit_Remark(self, node: Remark):
        pass  # No se necesita hacer nada específico para "Remark"

    def visit_For(self, node: For):
        self.visit(node.low)
        self.code.append(('LOCAL_SET', node.ident.var))

        self.code.append(('LOOP', ))

        self.visit(node.top)
        self.code.append(('CONSTI', 1))
        self.code.append(('ADDI', ))
        self.code.append(('LOCAL_GET', node.ident.var))
        self.code.append(('LEI', ))
        self.code.append(('CBREAK', ))

        if node.step:
            self.visit(node.step)
            self.step_stack.append(node.step)
        else:
            self.step_stack.append(1)

    def visit_Next(self, node: Next):
        self.code.append(('LOCAL_GET', node.ident.var))
        step = self.step_stack.pop()
        self.code.append(('CONSTI', step))
        self.code.append(('ADDI',))
        self.code.append(('LOCAL_SET', node.ident.var))
        self.code.append(('ENDLOOP',))

    def visit_Binary(self, node: Binary):
        self.visit(node.left)
        self.visit(node.right)
        op_map = {'+': 'ADDI', '-': 'SUBI', '*': 'MULI', '/': 'DIVI', '=': 'EQI', '<>': 'NEI', '<=': 'LEI', '<': 'LTI', '>=': 'GEI', '>': 'GTI'}
        if node.op in op_map:
            self.code.append((op_map[node.op],))

    def visit_Logical(self, node: Logical):
        self.visit(node.left)
        self.visit(node.right)
        op_map = {'=': 'EQI', '<>': 'NEI', '<=': 'LEI', '<': 'LTI', '>=': 'GEI', '>': 'GTI'}
        if node.op in op_map:
            self.code.append((op_map[node.op],))
    
    def visit_Unary(self, node: Unary):
        self.visit(node.expr)
        if node.op == '-':
            self.code.append(('NEG',))

    def visit_Variable(self, node: Variable):
        self.code.append(('LOCAL_GET', node.var))

    def visit_Number(self, node: Number):
        self.code.append(('CONSTI', node.value))
    
    def visit_Def(self, node: Def):
        fname = node.fn.name
        self.visit(node.expr)
        self.code.append(('CALL', fname))

    def visit_Call(self, node: Call):
        for e in node.expr:
            self.visit(e)
        self.code.append(('CALL', node.name))

    def visit_Stop(self, node: Stop):
        self.code.append(('RET', ))

    def visit_End(self, node: End):
        self.code.append(('RET', ))

    def generate(self, program):
        for lineno, statement in program.lines.items():
            self.code.append(('LINE', lineno))
            self.visit(statement)
        return self.code

def main():
    context = None
    l = Lexer()
    p = Parser(context)
    
    import sys

    if len(sys.argv) != 2:
        print("Uso: python basircode.py <archivo.bas>")
        sys.exit(1)

    source_file = sys.argv[1]
    with open(source_file, 'r') as file:
        source_code = file.read()

    tokens = l.tokenize(source_code)
    ast = p.parse(tokens)

    generator = IR_Visitor()
    generated_code = generator.generate(ast)
    print(generated_code)

    i = Interpreter()
    i.add_function('main', [], generated_code)
    i.execute('main')

if __name__ == "__main__":
    main()