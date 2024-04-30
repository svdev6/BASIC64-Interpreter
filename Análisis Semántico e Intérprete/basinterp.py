# basinterp.py

'''
Analisis Semántico & Intérprete para BASIC DARTMOUTH 64
'''

import sys
import math
import time
import random

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
    def __init__(self, prog, verbose = False):
        self.prog = prog
        self.verbose = verbose
        self.start_time = time.time() # Capturar el tiempo desde que inició el intérprete

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
            'TIME'  : self.get_time,
            'LEN'   : self.len_str,
            'LEFT$' : lambda x,n  : x[:n],
            'MID$'  : lambda x,m,n: x[m:n],
            'RIGHT$': lambda x,n : x[-n:],
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
            'time'  : self.get_time,
            'len'   : self.len_str,
            'left$' : lambda x,n  : x[:n],
            'mid$'  : lambda x,m,n: x[m:n],
            'right$': lambda x,n : x[-n:] 
        }
    
    @classmethod
    def interpret(cls, prog:Dict[int, Statement], verbose):
        basic = cls(prog, verbose)
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
            self.error(f"{instr.op} Los operandos deben ser numéricos")

    def _check_numeric_operand(self, instr, value):
        if isinstance(value, Union[int, float]):
            return True
        else:
            self.error(f"{instr.op} El operando debe ser numérico")

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

    # Interprete

    # Analisis Semantico (chequeos)
    def collect_data(self):
        '''
        Organizar los datos en la instrucción DATA dentro de una list
        Revisar las instrucciones READ / DATA
        '''

        self.data = []
        for lineno in self.stat:
            if isinstance(self.prog[lineno], Data):
                self.data += self.prog[lineno].numlist
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
            self.error("No hay instrucción END")

        if has_end != lineno:
            self.error("END no es la última instrucción")

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
                    self.error("Instrucción FOR sin NEXT en la linea %s" % self.stat[pc])

    # Instrucción GOTO
    def goto(self, lineno):
        if not lineno in self.prog:
            self.error(f"Linea de destino no definida en instrucción GOTO, ubicada en {self.stat[self.pc]}")
        self.pc = self.stat.index(lineno)

    # Calcular el tiempo desde que se inició el intérprete
    def get_time(self):
        return time.time() - self.start_time
    
    def len_str(self, expr):
        # Check if the argument is a string
        if isinstance(expr, str):
            return len(expr)  # Return the length of the string
        else:
            self.error(f"La función LEN() espera obtener un string, se obtuvo: {type(expr).__name__}")

    # Función que inicializa y corre el intérprete de BASIC
    def run(self):
        # Tabla de Simbolos
        self.vars   = {}        # Todas las variables
        self.lists  = {}        # Lista de variables
        self.tables = {}        # Tablas
        self.loops  = []        # Ciclos activos
        self.loopend = {}       # Saber cuando termina un ciclo
        self.gosub  = None      # Retorno para Gosub
        self.column = 0         # Control de columnas para Print

        self.stat = list(self.prog) # Ordenar lista de todas las lineas del programa
        self.stat.sort()
        self.pc   = 0           # Contador de programa

        # Preprocesamiento antes de ejecutar
        self.collect_data()     # Recoger todas las instrucciones DATA
        self.check_end()        # Verificar la instrucción END
        self.check_loops()      # Verificar ciclos FOR/NEXT
        
        while True:
            line  = self.stat[self.pc]
            instr = self.prog[line]

            try:
                if self.verbose:
                    print(line, instr.__class__.__name__)
                instr.accept(self)
            except BasicContinue as e:
                continue

            self.pc += 1

    # Asignaciones
    '''
    def assign(self, target, value):
        var, dim1, dim2 = target
        lineno = self.stat[self.pc]
        if not dim1 and dim2:
            self.vars[var] = value.accept(self)
        elif dim1 and not dim2:
            # Asignación de lista
            x = dim1.accept(self)
            if not var in self.lists:
                self.lists[var] = [0] * 10
            if x > len(self.lists[var]):
                self.error(f"Dimensión muy larga en la linea {lineno}")
            self.lists[var][x - 1] = value.accept(self)
        elif dim1 and dim2:
            x = dim1.accept(self)
            y = dim2.accept(self)
            if not var in self.tables:
                temp = [0] * 10
                v = []
                for i in range(10):
                    v.append(temp[:])
                self.tables[var] = v
            # Si la variable ya existe
            if x > len(self.tables[var]) or y > len(self.tables[var][0]):
                self.error(f"Dimensión muy larga en la linea {lineno}")
            self.tables[var][x - 1][y - 1] = value.accept(self)
    '''

    def assign(self, target, value):
        if isinstance(target, Variable):
            var = target.var
            dim1 = target.dim1
            dim2 = target.dim2
            lineno = self.stat[self.pc]
            if dim1 is None and dim2 is None:
                self.vars[var] = value.accept(self)
            elif dim1 is not None and dim2 is None:
                # Asignación de lista para arreglo unidimensional
                x = dim1.accept(self)
                if not var in self.lists:
                    self.lists[var] = [0] * 10

                if x > len(self.lists[var]):
                    self.error(f"Dimensión muy larga en la linea {lineno}")
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
                    self.error("Dimensiones muy largas en la linea {lineno}")
                self.tables[var][x - 1][y - 1] = value.accept(self)

    # Patrón Visitor para las instrucciones de BASIC64
    def visit(self, instr: Let):
        var = instr.var
        value = instr.expr
        self.assign(var, value)

    def visit(self, instr: Read):
        for target in instr.varlist:
            if self.dc >= len(self.data):
                # No hay más datos para procesar. El programa termina de ejecutarse
                raise BasicExit()
            value = self.data[self.dc]
            self.assign(target, value)
            self.dc += 1

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
                self.pad(15)
            elif pitem == ';':
                self.pad(3)
            elif isinstance(pitem, str):
                self.print_string(pitem)
            elif isinstance(pitem, (int, float)):
                self.print_string(f'{pitem:g}')
            else:
                print(pitem)
                self.error(f"Elemento {pitem} inesperado dentro de la instrucción PRINT en la linea {self.stat[self.pc]}")

        if (not items) or items[-1] not in (',', ';'):
            self.newline()

    def visit(self, instr: Input):
        label = instr.label
        # Asegurarse de que 'label' es un string
        if isinstance(label, tuple):
        # Convertir la tupla en un string, uniendo sus elementos con un separador
            label = ' '.join(str(item) for item in label if item is not None)

        if label:
            # Escribir mensaje antes de solicitar la entrada de datos
            sys.stdout.write(label)

        for variable in instr.vlist:
            value = input()
            if variable.var[-1] == '$':
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
            print(f"NEXT sin FOR en la linea {lineno}")
            return
        nextvar = instr.ident
        self.pc = self.loops[-1][0]
        loopinst = self.prog[self.stat[self.pc]]
        forvar = loopinst.ident
        if nextvar != forvar:
            print(f"NEXT no concuerda con FOR en la linea {lineno}")
            return
        raise BasicContinue()

    def visit(self, instr: Union[End, Stop]):
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
            print(f"Ya se está presentando una subrutina en la linea {lineno}")
            return
        self.gosub = self.stat[self.pc]
        self.goto(newline)
        raise BasicContinue()

    def visit(self, instr: Return):
        lineno = self.stat[self.pc]
        if not self.gosub:
            print(f"Instrucción RETURN sin GOSUB en la linea {lineno}")
            return
        self.goto(self.gosub)
        self.gosub = None

    '''
    def visit(self, instr: Dim):
        for vname, dim1, dim2 in instr.dimlist:
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
    '''

    '''

    def visit(self, instr: Dim):
        for item in instr.dimlist:
            if isinstance(item, Variable):
                varname = item.var
                dim1 = item.dim1.accept(self)
                dim2 = item.dim2.accept(self) if hasattr(item, 'dim2') else None  # Second dimension
            
                if dim2 is None:
                    self.lists[varname] = [0] * dim1  # 1D array
                else:
                    self.tables[varname] = [[0] * dim2 for _ in range(dim1)]  # 2D array
            else:
                self.error("Instrucción DIM errónea")
    '''

    def visit(self, instr: Dim):
        for item in instr.dimlist:
            if isinstance(item, Variable):
                vname = item.var
                dim1 = item.dim1
                dim2 = item.dim2

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

        # Si la función no cuenta con argumentos, como la función TIME()
        if expr is None:
            return self.functions[name]()
        else:
            expr = expr.accept(self)
            return self.functions[name](expr)

    def visit(self, instr: Call):
        name = instr.name  # Nombre de la función
        expr = instr.expr.accept(self)  # Argumento pasado a la función
    
        # Asegurarse de que la función exista
        if name not in self.functions:
            self.error(f"Función {name} no definida")

        # Llamar la función
        return self.functions[name](expr)
    
    def visit(self, instr: Variable):
        var = instr.var
        dim1 = instr.dim1
        dim2 = instr.dim2
        lineno = self.stat[self.pc]
        if not dim1 and not dim2:
            if var in self.vars:
                return self.vars[var]
            else:
                self.error(f"Variable '{var}' no definida en la linea {lineno}")
  
        # Evaluación de arreglo unidimensional (lista)
        if var in self.lists:
            x = dim1.accept(self)
            if x < 1 or x > len(self.lists[var]):
                self.error(f'El índice de la lista se salió de su límite en la linea {lineno}')
            if self.lists[var][x - 1]:
                return self.lists[var][x - 1]
            else:
                self.error(f"Arreglo unidimensional '{var}' no definido en la linea {lineno}")
      
        if dim1 and dim2:
            if var in self.tables:
                x = dim1.accept(self)
                y = dim2.accept(self)
                if x < 1 or x > len(self.tables[var]) or y < 1 or y > len(self.tables[var][0]):
                    self.error(f'Los índices de la tabla se salieron de sus límites en la linea {lineno}')
                return self.tables[var][x - 1][y - 1]
            else:
                self.error(f"Arreglo bidimensional '{var}' no definido en la linea {lineno}")
            
    def visit(self, instr: Union[Binary, Logical]):
        left = instr.left.accept(self)
        right = instr.right.accept(self)
        if instr.op == '+':
            (isinstance(left, str) and isinstance(right, str)) or self._check_numeric_operands(instr, left, right)
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
            self.error(f"Operador incorrecto {instr.op}")

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
