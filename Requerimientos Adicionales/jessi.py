from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from basparse import Parser
from baslex import Lexer
from basast import *  # Asegúrate de importar correctamente

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
        self.current_function = Function(name='_init', args=[], return_type='void', locals={})
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

    def visit_Program(self, node: Program):
        print(f'Visiting Program node with lines: {node.lines}')  # Añadir impresión de los nodos del programa
        for stmt in node:
            print(f'Visiting statement: {stmt}')
            self.visit(stmt)

    def visit_Let(self, node: Let):
        # Evaluar la expresión y luego almacenar el resultado en la variable
        self.visit(node.expr)
        self.emit('LOCAL_SET', node.var.var)

    def visit_Variable(self, node: Variable):
        self.emit('LOCAL_GET', node.var)

    def visit_Number(self, node: Number):
        if isinstance(node.value, int):
            self.emit('CONSTI', node.value)
        elif isinstance(node.value, float):
            self.emit('CONSTF', node.value)
        else:
            raise ValueError("Invalid number type")
        
    def visit_int(self, node: int):
        self.emit('CONSTI', node)
    
    def visit_Print(self, node: Print):
        for expr in node.plist:
            if isinstance(expr, list):
                for subexpr in expr:
                    self.visit(subexpr)
            elif isinstance(expr, str):
                self.emit('CONSTS', expr)
                self.emit('PRINTS')  # Assuming PRINTS is for printing strings
            else:
                self.visit(expr)
                self.emit('PRINTI')  # Assuming PRINTI is for printing integers

    def visit_For(self, node: For):
        start_label = self.new_label('for_start')
        end_label = self.new_label('for_end')

        # Inicializar el valor del índice
        self.visit(node.low)
        self.emit('LOCAL_SET', node.ident.var)

        self.emit_label(start_label)

        # Condición de fin
        self.visit(node.top)
        self.emit('LOCAL_GET', node.ident.var)
        self.emit('GTI')
        self.emit('CBREAK', end_label)

        # Cuerpo del bucle
        self.visit(node.ident)  # Acceder a la variable de control del bucle
        self.emit('LOCAL_GET', node.ident.var)
        if node.step:
            self.visit(node.step)
        else:
            self.emit('CONSTI', 1)
        self.emit('ADDI')
        self.emit('LOCAL_SET', node.ident.var)

        self.emit('CONTINUE', start_label)
        self.emit_label(end_label)

    def visit_Next(self, node: Next):
        pass  # No se necesita hacer nada específico para "Next"

    def visit_End(self, node: End):
        self.emit('RET')

    def new_label(self, prefix):
        label = f'{prefix}_{len(self.stack)}'
        self.stack.append(label)
        return label

    def emit_label(self, label):
        self.emit(label + ':')

    def visit_Remark(self, node: Remark):
        pass  # No se necesita hacer nada específico para "Remark"

    def visit_list(self, node):
        for item in node:
            self.visit(item)

    def visit_String(self, node: String):
        self.emit('CONSTS', node.value)

    def visit_IfStatement(self, node):
        true_label = self.new_label('if_true')
        end_label = self.new_label('if_end')
        
        # Evaluar la expresión de la condición
        self.visit(node.relexpr)
        self.emit('CBRANCH', true_label)
        
        # Si la condición es falsa, salta al final
        self.emit('JUMP', end_label)
        
        # Etiqueta para el bloque verdadero
        self.emit_label(true_label)
        
        # Visitar el bloque verdadero
        self.visit(node.lineno)
        
        # Si hay un bloque "else", salta al final después de ejecutar el bloque verdadero

        
        # Etiqueta para el final
        self.emit_label(end_label)

    
    def visit_Goto(self, node: Goto):
        self.emit('JUMP', node.lineno)
    
    def visit_Data(self, node: Data):
        for data in node.mixedlist:
            if isinstance(data, str):
                self.emit('DATA_STRING', data)
            else:
                self.emit('DATA_NUMERIC', data.value)
    
    def visit_Read(self, node: Read):
        for var in node.varlist:
            self.emit('READ', var.var)
    
    def visit_Stop(self, node: Stop):
        self.emit('STOP')
    
    def visit_Def(self, node: Def):
        self.current_function = Function(name=node.fn, args=[], return_type='void', locals={})
        self.module.functions[node.fn] = self.current_function
        
        # Almacenar los parámetros en la función
        for arg in node.args:
            self.current_function.args.append(arg.var)
            self.current_function.locals[arg.var] = arg.type
        
        # Visitar el cuerpo de la función
        for stmt in node.body:
            self.visit(stmt)
            
        # Añadir un "RET" al final de la función
        self.emit('RET')
        
        # Restaurar la función actual
        self.current_function = self.module.functions['_init']
    
    def visit_GoSub(self, node: GoSub):
        self.emit('CALL', node.lineno)
    
    def visit_Return(self, node: Return):
        self.emit('RET')
    
    def visit_Dim(self, node: Dim):
        pass  # No se necesita hacer nada específico para "Dim"
    
    def visit_Binary(self, node: Binary):
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
    
    def visit_Logical(self, node: Logical):
        pass  # No se necesita hacer nada específico para "Logical"
    
    def visit_Unary(self, node: Unary):
        self.visit(node.expr)
        if node.op == 'not':
            self.emit('NOT')
    
    def visit_Literal(self, node: Literal):
        pass  # No se necesita hacer nada específico para "Literal"
    
    def visit_Group(self, node: Group):
        self.visit(node.expr)
    
    def visit_Bltin(self, node: Bltin):
        for expr in node.expr:
            self.visit(expr)
        self.emit('CALL', node.name)
    
    def visit_Input(self, node: Input):
        for var in node.vlist:
            self.emit('INPUT', var.var)
    
    def visit_Call(self, node: Call):
        for expr in node.expr:
            self.visit(expr)
        self.emit('CALL', node.name)
    
    def visit_Restore(self, node: Remark):
        self.emit('RESTORE')


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
