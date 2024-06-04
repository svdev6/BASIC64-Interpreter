from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from basparse import Parser
from baslex import Lexer
from basast import Program, Remark, Print, End  # Asegúrate de importar correctamente

# Clase para representar una instrucción IR
@dataclass
class Instruction:
    operation: str
    operands: Tuple[Any, ...]

# Clase para representar una función en el módulo
@dataclass
class Function:
    name: str
    args: List[str]
    return_type: str
    locals: Dict[str, str]
    body: List[Instruction] = field(default_factory=list)

# Clase para representar un módulo que contiene múltiples funciones
@dataclass
class Module:
    functions: Dict[str, Function] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)

class CodeGenerator:
    def __init__(self):
        self.module = Module()
        self.current_function = Function(name='__init', args=[], return_type='void', locals={})
        self.module.functions['_init'] = self.current_function
        self.stack = []

    def visit_NoneType(self, node):
        pass

    def generate(self, program):        
        if isinstance(program, Program):
            for stmt in program.lines.values():  # Accede a los valores del diccionario lines
                self.visit(stmt)
        else:
            print("Tipo de programa encontrado no coincide con Program")
            raise ValueError("Expected a Program node as input.")


        # Añadir un "RET" al final de la función "_init"
        self.emit('RET')

        return self.module

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        print(f'Visiting node: {method_name}')  # Añadir impresión del nodo visitado
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f'No visit_{type(node).__name__} method')

    def emit(self, operation, *operands):
        instr = Instruction(operation, operands)
        self.current_function.body.append(instr)
        print(f'Emitted instruction: {instr}')  # Añadir impresión de la instrucción emitida

    def visit_Program(self, node):
        print(f'Visiting Program node with lines: {node.lines}')  # Añadir impresión de los nodos del programa
        for stmt in node:
            print(f'Visiting statement: {stmt}')
            self.visit(stmt)

    def visit_Let(self, node):
        # Evaluar la expresión y luego almacenar el resultado en la variable
        self.visit(node.expr)
        self.emit('LOCAL_SET', node.var.var)

    def visit_Variable(self, node):
        self.emit('LOCAL_GET', node.var)

    def visit_Number(self, node):
        self.emit('CONSTI', node.value)

    def visit_Print(self, node):
        for expr in node.plist:
            if isinstance(expr, list):
                for subexpr in expr:
                    self.visit(subexpr)
            else:
                self.visit(expr)
            self.emit('PRINTI')

    def visit_For(self, node):
        start_label = self.new_label('for_start')
        end_label = self.new_label('for_end')
        
        # Inicializar el valor del índice
        self.visit(node.low)
        self.emit('LOCAL_SET', node.ident.var)
        
        self.emit_label(start_label)
        
        # Condición de fin
        self.visit(node.ident)
        self.visit(node.top)
        self.emit('GTI')
        self.emit('CBREAK', end_label)
        
        # Cuerpo del bucle
        for stmt in node.body:
            self.visit(stmt)
        
        # Incrementar el valor del índice
        self.visit(node.ident)
        if node.step:
            self.visit(node.step)
        else:
            self.emit('CONSTI', 1)
        self.emit('ADDI')
        self.emit('LOCAL_SET', node.ident.var)
        
        self.emit('CONTINUE', start_label)
        self.emit_label(end_label)

    def visit_Next(self, node):
        pass  # No se necesita hacer nada específico para "Next"

    def visit_End(self, node):
        self.emit('RET')

    def new_label(self, prefix):
        label = f'{prefix}_{len(self.stack)}'
        self.stack.append(label)
        return label

    def emit_label(self, label):
        self.emit(label + ':')

    def visit_Remark(self, node):
        pass  # No se necesita hacer nada específico para "Remark"

    def visit_list(self, node):
        for item in node:
            self.visit(item)

    def visit_String(self, node):
        self.emit('CONSTS', node.value)

def main():
    import sys

    if len(sys.argv) != 2:
        print("Uso: python basircode.py <archivo.bas>")
        sys.exit(1)

    source_file = sys.argv[1]

    # Inicializar el lexer
    lexer = Lexer()

    # Crear una instancia de Parser con un contexto
    context = None  # Aquí puedes pasar cualquier contexto necesario
    parser = Parser(context)

    with open(source_file, 'r') as file:
        source_code = file.read()

    tokens = lexer.tokenize(source_code)
    ast = parser.parse(tokens)
    print("Tipo de programa recibido:", type(ast))
    print("Contenido del AST:", ast)
    
    # Generar el código intermedio a partir del AST
    codegen = CodeGenerator()
    module = None  # Inicializamos module en None
    try:
        module = codegen.generate(ast)
    except ValueError as e:
        print("Error en la generación de código:", e)

    # Imprimir el código intermedio si module no es None
    if module:
        for func in module.functions.values():
            print(f'Function: {func.name}')
            for instr in func.body:
                print(f'  {instr}')

if __name__ == "__main__":
    main()