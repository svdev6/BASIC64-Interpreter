# basinterp.py

'''
Analisis Semántico & Intérprete para BASIC DARTMOUTH 64
'''

import sys
import math
import time
import random
import psutil
from contextlib import redirect_stdout

from typing import Dict, Union
from basast import *

class BasicExit(BaseException):
    pass

class BasicContinue(Exception):
    pass

def _is_truthy(value):
    if value is None:
        return False
    elif isinstance(value, bool):
        return value
    else:
        return True

class Interpreter(Visitor):
    def __init__(self, prog, verbose = False, uppercase = False, array_base = 1, slicing = False, go_next = False, trace = False, tabs = 15, random_seed = None, fname = None, print_stats = False, write_stats = False, input_file = None):
        self.prog = prog
        self.verbose = verbose
        self.uppercase = uppercase
        self.array_base = array_base
        self.slicing = slicing
        self.go_next = go_next
        self.trace = trace
        self.tabs = tabs
        self.random_seed = random_seed
        if self.random_seed is not None:
            random.seed(self.random_seed)  # Semilla para el generador de números aleatorios
        self.dc = 0
        self.start_time = time.time() # Capturar el tiempo desde que inició el intérprete
        self.pc = 0  # Contador de instrucciones ejecutadas
        self.memory_used = 0  # Uso de memoria
        self.fname = fname # Nombre del archivo
        self.print_stats = print_stats # Imprimir estadísticas en pantalla
        self.write_stats = write_stats # Escribir estadísticas en archivo de texto
        self.input_file = input_file
        self.input_lines = []
        if self.input_file:
            with open(self.input_file, 'r') as f:
                self.input_lines = f.readlines()
        self.input_index = 0

        # Diccionario de funciones predefinidas
        self.functions = {
            'SIN'   : lambda x: math.sin(x),
            'COS'   : lambda x: math.cos(x),
            'TAN'   : lambda x: math.tan(x),
            'ATN'   : lambda x: math.atan(x),
            'EXP'   : lambda x: math.exp(x),
            'ABS'   : lambda x: abs(x),
            'LOG'   : lambda x: math.log(x),
            'SQR'   : lambda x: math.sqrt(x),
            'INT'   : lambda x: int(x),
            'RND'   : lambda x: random.random(),
            'TAB'   : lambda x: ' '*x,
            'DEG'   : lambda x: x * (180.0/3.141592654),
            'PI'    : self.return_pi,
            'TIME'  : self.get_time,
            'LEN'   : self.len_str,
            'LEFT$' : lambda x,n  : x[:n],
            'RIGHT$': lambda x,n : x[-n:],
            'CHR$'  : self.get_ascii,
            'sin'   : lambda x: math.sin(x),
            'cos'   : lambda x: math.cos(x),
            'tan'   : lambda x: math.tan(x),
            'atn'   : lambda x: math.atan(x),
            'exp'   : lambda x: math.exp(x),
            'abs'   : lambda x: abs(x),
            'log'   : lambda x: math.log(x),
            'sqr'   : lambda x: math.sqrt(x),
            'int'   : lambda x: int(x),
            'rnd'   : lambda x: random.random(),
            'tab'   : lambda x: ' '*x,
            'deg'   : lambda x: x * (180.0/3.141592654),
            'pi'    : self.return_pi,
            'time'  : self.get_time,
            'len'   : self.len_str,
            'left$' : lambda x,n  : x[:n],
            'right$': lambda x,n : x[-n:],
            'chr$'  : self.get_ascii,
        }
    
    @classmethod
    def interpret(cls, prog:Dict[int, Statement], verbose, uppercase, array_base, slicing, go_next, trace, tabs, random_seed, fname, print_stats, write_stats, input_file):
        basic = cls(prog, verbose, uppercase, array_base, slicing, go_next, trace, tabs, random_seed, fname, print_stats, write_stats, input_file)
        try:
            basic.run()
        except BasicExit:
            pass

    def error(self, message):
        sys.stderr.write(message)
        raise BasicExit()

    def _check_numeric_operands(self, instr, left, right):
        if isinstance(left, Union[int, float]) and isinstance(right, Union[int, float]):
            return True
        else:
            self.error(f"{instr.op} The operands must be numeric")

    def _check_numeric_operand(self, instr, value):
        if isinstance(value, Union[int, float]):
            return True
        else:
            self.error(f"{instr.op} The operand isn't numeric")

    # Método Print según Peter Norvig
    def print_string(self, s) -> None:
        print(s, end='')
        self.column += len(s)
        if self.column >= 80:
            self.newline()

    def pad(self, width) -> None:
        while self.column % width != 0:
            self.print_string(' ')

    def newline(self):
        print(); self.column = 0

    # Intérprete

    # Analisis Semantico (chequeos)
    def collect_data(self):
        '''
        Organizar los datos en la instrucción DATA dentro de una list
        Revisar las instrucciones READ / DATA
        '''

        self.data = []
        for lineno in self.stat:
            if isinstance(self.prog[lineno], Data):
                # Process each item in the mixed list
                for item in self.prog[lineno].mixedlist:
                    if isinstance(item, str):
                        # If it's a string, add it directly to the data
                        self.data.append(item)
                    else:
                        # If it's an AST node, call accept to get its value
                        self.data.append(item.accept(self))
        self.dc = 0

    def check_end(self):
        '''
        Un programa en BASIC solo debe contener una instrucción END
        y esta debe de estar en la ultima linea.
        '''
        has_end = False

        for lineno in self.stat:
            if isinstance(self.prog[lineno], End) and not has_end:
                has_end = lineno

        if not has_end:
            self.error("Undefined END instruction")

        if has_end != lineno:
            self.error("END is not the last instruction")

    def check_loops(self):
        for pc in range(len(self.stat)):
            lineno = self.stat[pc]
            if isinstance(self.prog[lineno], For):
                forinst = self.prog[lineno]
                loopvar = forinst.ident
                for i in range(pc + 1, len(self.stat)):
                    if isinstance(self.prog[self.stat[i]], Next):
                        nextvar = self.prog[self.stat[i]].ident
                        if nextvar != loopvar:
                            continue
                        self.loopend[pc] = i
                        break
                else:
                    self.error("FOR without NEXT at line %s" % self.stat[pc])

    # Instrucción GOTO
    def goto(self, lineno):
        if not lineno in self.prog:
            if self.go_next:
                self.pc += 1
                return
            else:
                self.error(f"Undefined line {lineno} in GOTO instruction, located at line {self.stat[self.pc]}")
        self.pc = self.stat.index(lineno)

    # Calcular el tiempo desde que se inició el intérprete
    def get_time(self):
        return time.time() - self.start_time
    
    def len_str(self, expr):
        # Verificar si el argumento es STRING
        if isinstance(expr, str):
            return len(expr)  # Retornar la longitud
        else:
            self.error(f"LEN() expected a string, was obtained: {type(expr).__name__}")

    def return_pi(self):
        return 3.141592654
    
    def get_ascii(self, expr):
        if isinstance(expr, Union[int, float]):
            return chr(expr)
        else:
            self.error(f"CHR$() expected a number, was obtained: {type(expr).__name__}")

    def print_statistics(self):
        time_elapsed = time.time() - self.start_time
        process = psutil.Process()
        self.memory_used = process.memory_info().rss
        print(f'This program took {time_elapsed:.2f} seconds to run')
        print(f'Memory usage: {self.memory_used} bytes')
        print(f"Total number of processed lines: {self.pc + 1}")

    # Función que inicializa y corre el intérprete de BASIC
    def run(self):
        # Tabla de Simbolos
        self.vars    = {}        # Todas las variables
        self.lists   = {}        # Lista de variables
        self.tables  = {}        # Tablas
        self.loops   = []        # Ciclos activos
        self.loopend = {}        # Saber cuando termina un ciclo
        self.gosub   = None      # Retorno para Gosub
        self.column  = 0         # Control de columnas para Print

        self.stat = list(self.prog) # Ordenar lista de todas las lineas del programa
        self.stat.sort()
        self.pc      = 0         # Contador de programa

        # Preprocesamiento antes de ejecutar
        self.collect_data()     # Recoger todas las instrucciones DATA
        self.check_end()        # Verificar la instrucción END
        self.check_loops()      # Verificar ciclos FOR/NEXT
        
        while True:
            line  = self.stat[self.pc]
            instr = self.prog[line]

            if self.trace:
                print(f"Executing line {self.stat[self.pc]}")  # Trace the current line

            try:
                if self.verbose:
                    print(line, instr.__class__.__name__)
                instr.accept(self)
            except BasicContinue as e:
                continue

            self.pc += 1


    # Asignaciones
    def assign(self, target, value):
        if isinstance(target, Variable):
            var = target.var
            dim1 = target.dim1
            dim2 = target.dim2
            lineno = self.stat[self.pc]
            if dim1 is None and dim2 is None:
                if isinstance(value, (int, float, str)):
                    self.vars[var] = value
                else:
                    self.vars[var] = value.accept(self)
            elif dim1 is not None and dim2 is None:
                # Asignación de lista para arreglo unidimensional
                x = dim1.accept(self)
                if not var in self.lists:
                    self.lists[var] = [0] * 10

                if x > len(self.lists[var]):
                    self.error(f"Dimension is too large at line {lineno}")

                if isinstance(value, (int, float, str)):
                    self.lists[var][x - 1] = value
                else:
                    self.lists[var][x - 1] = value.accept(self)
    
            elif dim1 is not None and dim2 is not None:
                x = dim1.accept(self)
                y = dim2.accept(self)
                if not var in self.tables:
                    temp = [0] * 10
                    v = []
                    for i in range(10):
                        v.append(temp[:])
                    self.tables[var] = v
                # Si la variable existe
                if x > len(self.tables[var]) or y > len(self.tables[var][0]):
                    self.error("Dimensions are too large at line {lineno}")
                
                if isinstance(value, (int, float, str)):
                    self.tables[var][x - 1][y - 1] = value
                else:
                    self.tables[var][x - 1][y - 1] = value.accept(self)

    # Patrón Visitor para las instrucciones de BASIC64
    def visit(self, instr: Let):
        var = instr.var
        value = instr.expr
        if self.slicing:
            self.error(f"Cannot proceed with LET instruction at line {self.stat[self.pc]}. String slicing might be enabled.")
        self.assign(var, value)

    def visit(self, instr: Read):
        for target in instr.varlist:
            if self.dc >= len(self.data):
                # No hay más datos para procesar. El programa termina de ejecutarse
                raise BasicExit()
            # Inicializar 'value' con un valor por defecto antes de usarlo
            value = self.data[self.dc]  # Get the current data item
        
            if isinstance(target.var, str) and target.var[-1] == '$':
                if self.slicing:
                    self.error(f"Cannot proceed with READ instruction at line {self.stat[self.pc]}. String slicing might be enabled.")
                # Si es una variable de tipo string ($), debe obtener una string
                value = value if isinstance(value, str) else str(value)  # Asegurarse de que sea una string
            else:
                # Si es una variable numérica, obtener el tipo correcto. Puede dar un mensaje de error si se activa el corte de cadena desde el compilador
                try:
                    value = float(value)  # Convertir a float
                except ValueError:
                    self.error(f"The value {value} could not be read.")
            self.assign(target, value)
            self.dc += 1

    def visit(self, instr: Restore):
        """
        Resetea el contador de DATA al principio para leer desde DATA nuevamente
        """
        self.dc = 0

    def visit(self, instr: Data):
        pass

    def visit(self, instr: Remark):
        pass

    def visit(self, instr: Print):
        items = instr.plist
        for pitem in items:

            while isinstance(pitem, list):
                pitem = pitem[0]
    
            if not pitem:
                continue
            if isinstance(pitem, Node):
                pitem = pitem.accept(self)
            if pitem == ',':
                self.pad(self.tabs)
            elif pitem == ';':
                self.pad(1)
            elif isinstance(pitem, str):
                self.print_string(pitem)
            elif isinstance(pitem, (int, float)):
                self.print_string(f'{pitem:g}')
            else:
                self.error(f"Unexpected element {pitem} inside PRINT instruction at line {self.stat[self.pc]}")

        if (not items) or items[-1] not in (',', ';'):
            self.newline()

    def visit(self, instr: Input):
        label = instr.label
        # Asegurarse de que 'label' es un string
        if isinstance(label, tuple):
        # Convertir la tupla en un string, uniendo sus elementos con un separador
            label = ' '.join(str(item) for item in label if item is not None)

        if label and not self.input_file:
            # Remover el separador
            label = label.rstrip(';').strip()
            label = label.rstrip(',').strip()
            # Escribir mensaje antes de solicitar la entrada de datos
            sys.stdout.write(label + " ")

        for variable in instr.vlist:
            if self.input_file:
            # Leer del archivo
                if self.input_index < len(self.input_lines):
                    value = self.input_lines[self.input_index].strip()
                    if variable.var[-1] == '$' and not self.slicing:
                        if self.slicing:
                            self.error(f"Cannot proceed with INPUT instruction at line {self.stat[self.pc]}. String slicing might be enabled.")
                        elif self.uppercase == True:
                            value = String(value.upper())
                        else:
                            value = String(value)
                    else:
                        try:
                            value = Number(int(value))
                        except ValueError:
                            value = Number(float(value))
                    self.assign(variable, value)
                    self.input_index += 1
                else:
                    self.error("No more input data available in the file.")

            else:
                value = input()
                if variable.var[-1] == '$':
                    if self.slicing:
                        self.error(f"Cannot proceed with INPUT instruction at line {self.stat[self.pc]}. String slicing might be enabled.")
                    elif self.uppercase == True:
                        value = String(value.upper())
                    else:
                        value = String(value)
                
                else:
                    try:
                        value = Number(int(value))
                    except ValueError:
                        value = Number(float(value))
                self.assign(variable, value)

    def visit(self, instr: Goto):
        newline = instr.lineno
        self.goto(newline)
        raise BasicContinue()

    def visit(self, instr: IfStatement):
        relexpr = instr.relexpr
        newline = instr.lineno
        if _is_truthy(relexpr.accept(self)):
            self.goto(newline)
            raise BasicContinue

    def visit(self, instr: For):
        loopvar = instr.ident
        initval = instr.low
        finval  = instr.top
        stepval = instr.step

        # Si no hay un valor de salto especificado, establecer un valor de 1 por defecto
        if stepval is None:
            stepval = Number(1)

        # Evaluar el valor de salto si existe
        stepval = stepval.accept(self)

        # Verificar si es un loop nuevo
        if not self.loops or self.loops[-1][0] != self.pc:
            # Parece ser un nuevo loop. Hacer la asignación inicial
            newvalue = initval
            self.assign(loopvar, initval)
            self.loops.append((self.pc, stepval))
        else:
            # Es la repetición de un ciclo anterior
            # Actualizar el valor de la variable del loop según el salto
            stepval = Number(self.loops[-1][1])
            newvalue = Binary('+', loopvar, stepval)
     
            if self.loops[-1][1] < 0:
                relop = '>='
            else:
                relop = '<='

            if not _is_truthy(Logical(relop, newvalue, finval).accept(self)):
                # El ciclo se ha completado. Saltar a la instrucción NEXT
                self.pc = self.loopend[self.pc]
                self.loops.pop()
            else:
                self.assign(loopvar, newvalue)

    def visit(self, instr: Next):
        lineno = self.stat[self.pc]
        if not self.loops:
            print(f"NEXT without FOR at line {lineno}")
            return
        nextvar = instr.ident
        self.pc = self.loops[-1][0]
        loopinst = self.prog[self.stat[self.pc]]
        forvar = loopinst.ident
        if nextvar != forvar:
            print(f"NEXT doesn't match FOR at line {lineno}")
            return
        raise BasicContinue()

    def visit(self, instr: Union[End, Stop]):
        if self.write_stats:
            base = self.fname.split('/')[-1]
            base1 = base.split('.')[0]
            fstats = base1 + '_stats.txt'
            print(f'Dumping text file with stats: {fstats}')
            with open(fstats, 'w', encoding='utf-8') as fout:
                with redirect_stdout(fout):
                    self.print_statistics()
            if self.print_stats:
                self.print_statistics()
            raise BasicExit()

        elif self.print_stats:
            self.print_statistics()
            raise BasicExit()
        
        else:
            raise BasicExit()
    
    def visit(self, instr: Def):
        fname = instr.fn
        pname = instr.ident
        expr = instr.expr

        def eval_func(pvalue, name = pname, self = self, expr = expr):
            self.vars[name] = pvalue  # Asignar el parámetro a su valor respectivo
            return expr.accept(self)  # Evaluar la expresión de la función
        self.functions[fname] = eval_func

    def visit(self, instr: GoSub):
        newline = instr.lineno
        lineno = self.stat[self.pc]
        if self.gosub:
            print(f"A subroutine is already in process at line {lineno}")
            return
        self.gosub = self.stat[self.pc]
        self.goto(newline)
        raise BasicContinue()

    def visit(self, instr: Return):
        lineno = self.stat[self.pc]
        if not self.gosub:
            print(f"RETURN without GOSUB at lien {lineno}")
            return
        self.goto(self.gosub)
        self.gosub = None

    def visit(self, instr: Dim):
        for item in instr.dimlist:
            if isinstance(item, Variable):
                vname = item.var
                dim1 = item.dim1
                dim2 = item.dim2

                if self.slicing:
                    self.error(f"The dimension at line {self.stat[self.pc]} could not be initialized. String slicing might be enabled.")

                if not dim2:
                    # Variable de una dimensión
                    x = dim1.accept(self)
                    self.lists[vname] = [0] * x
                else:
                    # Variable de doble dimensión
                    x = dim1.accept(self)
                    y = dim2.accept(self)
                    temp = [0] * y
                    v = []
                    for i in range(x):
                        v.append(temp[:])
                    self.tables[vname] = v

    # Patrón Visitor para expresiones y más (Bltin, Call)
    def visit(self, instr: Group):
        return instr.expr.accept(self)
    
    def visit(self, instr: Bltin):
        name = instr.name
        expr = instr.expr

        # Implementación propia para MID$()
        if (name == "MID$") or (name == "mid$"):
            if isinstance(expr, list) and len(expr) == 3:
                str_val = expr[0].accept(self)  # La cadena original 
                start = expr[1].accept(self)  # Índice de inicio
                length = expr[2].accept(self)  # Longitud
                return str_val[start - 1 : start - 1 + length]
            else:
                self.error("Incorrect parameters for MID$")

        # Si la función no cuenta con argumentos, como la función TIME()
        elif expr is None:
            return self.functions[name]()
        
        # Si la función cuenta con por lo menos un argumento
        elif expr:
            if isinstance(expr, list): # Si son múltiples argumentos, inicializar los elementos de la lista de argumentos
                processed_expr = [e.accept(self) for e in expr]
                return self.functions[name](*processed_expr)
            if isinstance(expr, Node):
                processed_expr = expr.accept(self) # Si es un solo argumento, inicializar directamente
                return self.functions[name](processed_expr)
        else:
            self.error(f"Undefined function {name}")

    def visit(self, instr: Call):
        name = instr.name  # Nombre de la función
        expr = instr.expr  # Argumento pasado a la función

        if isinstance(expr, list):
        # Procesa la lista de argumentos, cada uno de estos siendo un nodo AST
            args = [e.accept(self) for e in expr]
            if name not in self.functions:
                self.error(f"Undefined function {name}")
            return self.functions[name](*args)  # Pasar el argumento de la función

        elif isinstance(expr, Node):
            # Si es un único nodo AST
            if name not in self.functions:
                self.error(f"Undefined function {name}")
            return self.functions[name](expr.accept(self))
    
    def visit(self, instr: Variable):
        var = instr.var
        dim1 = instr.dim1
        dim2 = instr.dim2
        lineno = self.stat[self.pc]
        if not dim1 and not dim2:
            if var in self.vars:
                return self.vars[var]
            else:
                self.error(f"Undefined variable '{var}' at line {lineno}")
  
        # Evaluación de arreglo unidimensional (lista)
        elif dim1 and not dim2:
            if var in self.lists:
                x = dim1.accept(self)
                if x < self.array_base or x > len(self.lists[var]):
                    self.error(f'Index of {var} is out of bounds at line {lineno}')
                return self.lists[var][x - 1]
      
        elif dim1 and dim2:
            if var in self.tables:
                x = dim1.accept(self)
                y = dim2.accept(self)
                x = int(x)
                y = int(y)
                if x < self.array_base or x > len(self.tables[var]) or y < self.array_base or y > len(self.tables[var][0]):
                    self.error(f'Indexes of {var} are out of bounds at line {lineno}')
                return self.tables[var][x - 1][y - 1]
            
        else:
            self.error(f"Undefined variable '{var}' at line {lineno}")
            
    def visit(self, instr: Union[Binary, Logical]):
        left = instr.left.accept(self)
        right = instr.right.accept(self)

        # Comparación entre strings
        if isinstance(left, str) and isinstance(right, str):
            if instr.op == '+':
                return left + right
            elif instr.op == '=':
                return left == right
            elif instr.op == '<>':
                return left != right
            elif instr.op == '<':
                return left < right
            elif instr.op == '<=':
                return left <= right
            elif instr.op == '>':
                return left > right
            elif instr.op == '>=':
                return left >= right
            else:
                self.error(f"Incorrect operator {instr.op}")
            
        # Operaciones entre valores numéricos
        if instr.op == '+':
            self._check_numeric_operands(instr, left, right)
            return left + right
        elif instr.op == '-':
            self._check_numeric_operands(instr, left, right)
            return left - right
        elif instr.op == '*':
            self._check_numeric_operands(instr, left, right)
            return left * right
        elif instr.op == '/':
            self._check_numeric_operands(instr, left, right)
            return left / right
        elif instr.op == '^':
            self._check_numeric_operands(instr, left, right)
            return math.pow(left, right)
        elif instr.op == '=':
            self._check_numeric_operands(instr, left, right)
            return left == right
        elif instr.op == '<>':
            self._check_numeric_operands(instr, left, right)
            return left != right
        elif instr.op == '<':
            self._check_numeric_operands(instr, left, right)
            return left < right
        elif instr.op == '>':
            self._check_numeric_operands(instr, left, right)
            return left > right
        elif instr.op == '<=':
            self._check_numeric_operands(instr, left, right)
            return left <= right
        elif instr.op == '>=':
            self._check_numeric_operands(instr, left, right)
            return left >= right
        else:
            self.error(f"Incorrect operator {instr.op}")

    def visit(self, instr: Unary):
        value = instr.expr.accept(self)
        if instr.op == '-':
            self._check_numeric_operand(instr, value)
            return - value
        pass

    def visit(self, instr: Literal):
        return instr.value
    
    def visit(self, instr: Node):
        lineno = self.stat[self.pc]
        print(lineno, instr.__class__.__name__)
