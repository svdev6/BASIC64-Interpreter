from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from basparse import Parser
from baslex import Lexer
from basast import *  # Asegúrate de importar correctamente
from interpir import Interpreter

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.label_count = 0

    def visit_NoneType(self, node):
        pass

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        print(f'Visiting node: {method_name}')  # Añadir impresión del nodo visitado
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        raise Exception(f'No visit_{type(node).__name__} method')
    
    def visit_Program(self, node: Program):
        print(f'Visiting Program node with lines: {node.lines}')  # Añadir impresión de los nodos del programa
        for stmt in node.lines.values():
            print(f'Visiting statement: {stmt}')
            self.visit(stmt)

    def visit_Let(self, node: Let):
        self.visit(node.expr)
        self.code.append(('LOCAL_SET', node.var))

    def visit_Variable(self, node: Variable):
        self.code.append(('LOCAL_GET', node.var))

    def visit_Number(self, node: Number):
        if isinstance(node.value, int):
            self.code.append(('CONSTI', node.value))
        elif isinstance(node.value, float):
            self.code.append(('CONSTF', node.value))
        else:
            raise ValueError("Invalid number type")

    def visit_int(self, node: int):
        self.code.append(('CONSTI', node))

    def visit_float(self, node: float):
        self.code.append(('CONSTF', node))

    def visit_Print(self, node: Print):
        print(f'Visiting Print node with plist: {node.plist}')
        for expr in node.plist:
            if isinstance(expr, list):
                for subexpr in expr:
                    self.visit(subexpr)
            elif isinstance(expr, str):
                print(f'Visiting String: {expr}')
                self.code.append(('CONSTS', expr))
                self.code.append(('PRINTS',))
            else:
                self.visit(expr)
                self.code.append(('PRINTI',))
    
    def visit_Remark(self, node: Remark):
        pass

    def visit_For(self, node: For):
        start_label = self.new_label()
        end_label = self.new_label()

        self.visit(node.low)
        self.code.append(('LOCAL_SET', node.ident))

        self.append_label(start_label)

        self.visit(node.top)
        self.code.append(('LOCAL_GET', node.ident))
        self.code.append(('GTI'))
        self.code.append(('CBREAK', end_label))

        self.visit(node.ident)
        self.code.append(('LOCAL_GET', node.ident))
        if node.step:
            self.visit(node.step)
            self.code.append(('CONSTI', node.step))
        else:
            self.code.append(('CONSTI', 1))
        self.code.append(('ADDI',))
        self.code.append(('LOCAL_SET', node.ident))

        self.code.append(('CONTINUE', start_label))
        self.append_label(end_label)

    def visit_Next(self, node: Next):
        self.code.append(('ADDI', ))
        self.code.append(('LOCAL_SET', node.ident.var))

    def visit_End(self, node: End):
        pass

    def new_label(self) -> str:
        label = f'L{self.label_count}'
        self.label_count += 1
        return label
    
    def append_label(self, label):
        self.code.append((label + ':',))
    
    def visit_list(self, node):
        for item in node:
            self.visit(item)
    
    def visit_String(self, node: String):
        print(f'Visiting String node with value: {node.value}')
        self.code.append(('CONSTS', node.value))

    def visit_IfStatement(self, node: IfStatement):
        true_label = self.new_label('if_true')
        end_label = self.new_label('if_end')

        self.visit(node.relexpr)
        self.code.append(('CBRANCH', true_label))

        self.code.append(('JUMP', end_label))

        self.append_label(true_label)

        self.visit(node.lineno)

        self.append_label(end_label)

    def visit_Goto(self, node: Goto):
        self.code.append(('JUMP', node.lineno))

    def visit_Data(self, node: Data):
        for data in node.mixedlist:
            if isinstance(data, str):
                self.code.append(('DATA_STRING', data))
            else:
                self.code.append(('DATA_NUMERIC', data))

    def visit_Read(self, node: Read):
        for var in node.varlist:
            self.code.append(('READ', var.var))

    def visit_Stop(self, node: Stop):
        pass

    def visit_GoSub(self, node: GoSub):
        self.code.append(('CALL', node.lineno))

    def visit_Return(self, node: Return):
        self.code.append(('RET',))

    def visit_Dim(self, node: Dim):
        self.code.append(('LOCAL_GET', node.var))
    
    def visit_Binary(self, node: Binary):
        self.visit(node.left)
        self.visit(node.right)
        if node.op == '+':
            if isinstance(node.left, int) and isinstance(node.right, int):
                self.code.append(('ADDI', ))
            else:
                self.code.append(('ADDF', ))
        elif node.op == '-':
            if isinstance(node.left, int) and isinstance(node.right, int):
                self.code.append(('SUBI', ))
            else:
                self.code.append(('SUBF', ))
        elif node.op == '*':
            if isinstance(node.left, int) and isinstance(node.right, int):
                self.code.append(('MULTI', ))
            else:
                self.code.append(('MULTF', ))
        elif node.op == '/':
            if isinstance(node.left, int) and isinstance(node.right, int):
                self.code.append(('DIVI', ))
            else:
                self.code.append(('DIVF', ))

    def visit_Logical(self, node: Logical):
        pass

    def visit_Unary(self, node: Unary):
        self.visit(node.expr)
        if node.op == '-':
            self.code.append(('NOT', ))
    
    def visit_Literal(self, node: Literal):
        pass

    def visit_Group(self, node: Group):
        self.visit(node.expr)

    def visit_Bltin(self, node: Bltin):
        if node.expr is not None:
            for expr in node.expr:
                self.visit(expr)
        # Aquí emites la instrucción correspondiente a la función intrínseca (en este caso, TIME())
        self.code.append(('CALL', node.name.upper()))

    def visit_Input(self, node: Input):
        for var in node.vlist:
            self.code.append(('INPUT', var.var))

    def visit_Call(self, node: Call):
        for expr in node.expr:
            self.visit(expr)
        self.code.append(('CALL', node.name))

    def visit_Restore(self, node: Restore):
        self.code.append(('RESTORE'))

def main():
    import sys

    if len(sys.argv) != 2:
        print("Uso: python basircode.py <archivo.bas>")
        sys.exit(1)

    source_file = sys.argv[1]

    lexer = Lexer()

    context = None
    parser = Parser(context)

    with open(source_file, 'r') as file:
        source_code = file.read()

    tokens = lexer.tokenize(source_code)
    ast = parser.parse(tokens)
    print("Tipo de programa recibido:", type(ast))
    print("Contenido del AST:", ast)

    codegen = CodeGenerator()
    codegen.visit(ast)
    print(codegen.code)

    i = Interpreter()
    i.add_function('main', [], codegen.code)
    i.execute('main')


if __name__ == "__main__":
    main()





    

    



    

    