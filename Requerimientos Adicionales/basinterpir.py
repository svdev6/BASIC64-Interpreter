# interp.py
'''
Proyecto del intérprete
=======================

Este es un intérprete que puede ejecutar programas BASIC directamente 
desde el código IR generado.

Para ejecutar un programa utilice:

    bash % python3 -m basic64.interp someprogram.bas

'''
import sys
import struct

class Interpreter:
  '''
  Ejecuta un intérprete del código intermedio generado para su compilador. 
  La idea de implementación es la siguiente. Dada una secuencia de tuplas 
  de instrucciones como:

     code = [
        ('CONSTI', 1),
        ('CONSTI', 2),
        ('ADDI',),
        ('PRINTI',)
        ...
     ]
 
  La clase ejecuta métodos self.run_opcode(args). Por ejemplo:

     self.run_CONSTI(1)
     self.run_CONSTI(2)
     self.run_ADDI()
     self.run_PRINTI()

  Sólo un recordatorio de que el código intermedio se basa en una máquina de pila.
  El intérprete necesita implementar la pila y la memoria para almacenar variables.
  '''
  def __init__(self):
    self.code = []
    self.pc = 0

    # Almacenamiento de variables
    self.globals = { }
    self.vars = { }

    # Pila frame stack
    self.frames = [ ]

    # La pila de operaciones
    self.stack = [ ]

    # Memoria
    self.memory = bytearray()

    # Rotulos flujo-control
    self.control = { }

    # Tabla de funciones
    self.functions = { }

    # Tabla de índices de instrucciones IR para 'GOTO'
    self.line_to_index = {}

  def push(self, value):
    self.stack.append(value)

  def pop(self):
    return self.stack.pop()

  def add_function(self, name, argnames, code):
    # muestra etiquetas de flujo de control
    control = { }
    levels = []
    for n, (inst, *args) in enumerate(code):
      if inst == 'IF':
        levels.append(n)
      elif inst == 'ELSE':
        control[levels[-1]] = n
        levels[-1] = n
      elif inst == 'ENDIF':
        control[levels[-1]] = n
        levels.pop()
      if inst == 'LOOP':
        levels.append(n)
      elif inst == 'CBREAK':
        levels.append(n)
      elif inst == 'ENDLOOP':
        control[n] = levels[-2]
        control[levels[-1]] = n
        levels.pop()
        levels.pop()
    self.functions[name] = (code, argnames, control)

  def execute(self, name):
    self.frames.append((self.code, self.pc, self.control, self.vars))
    self.code, argnames, self.control = self.functions[name]
    self.vars = { }

    # Map line numbers to instruction indices
    for idx, (inst, *args) in enumerate(self.code):
      if inst == 'LINE':
          self.line_to_index[args[0]] = idx

    for argname in argnames[::-1]:
      value = self.pop()
      self.vars[argname] = value

    self.pc = 0
    while self.pc < len(self.code):
      inst, *args = self.code[self.pc]
      getattr(self, f'run_{inst}')(*args)
      self.pc += 1
    self.code, self.pc, self.control, self.vars = self.frames.pop()

  # Interpreter opcodes
  def run_CONSTI(self, value):
    print(f"Executing CONSTI/CONSTF with value {value}")
    self.push(value)
  run_CONSTF = run_CONSTI

  def run_NEG(self):
        value = self.pop()
        self.push(-value)

  def run_ADDI(self):
    print(f"Executing ADDI/ADDF")
    self.push(self.pop() + self.pop())
  run_ADDF = run_ADDI

  def run_SUBI(self):
    print(f"Executing ADDI/ADDF")
    right = self.pop()
    left = self.pop()
    self.push(left-right)
  run_SUBF = run_SUBI

  def run_MULI(self):
    print(f"Executing ADDI/ADDF")
    self.push(self.pop() * self.pop())
  run_MULF = run_MULI

  def run_DIVI(self):
    print(f"Executing ADDI/ADDF")
    right = self.pop()
    left = self.pop()
    self.push(left // right)

  def run_DIVF(self):
    print(f"Executing ADDI/ADDF")
    right = self.pop()
    left = self.pop()
    self.push(left / right)

  def run_ITOF(self):
    self.push(float(self.pop()))

  def run_FTOI(self):
    self.push(int(self.pop()))

  def run_PRINTI(self):
    print("Executing PRINTI/PRINTF")
    try:
      print(self.pop())
    except:
      pass
  run_PRINTF = run_PRINTI

  def run_PRINTB(self):
      try:
        print(chr(self.pop()),end='')
      except:
        pass

  def run_LOCAL_GET(self, name):
    print(f"Executing LOCAL_GET with variable {name}")
    self.push(self.vars[name])

  def run_GLOBAL_GET(self, name):
    print(f"Executing GLOBAL_GET with variable {name}")
    self.push(self.globals[name])

  def run_LOCAL_SET(self, name):
    print(f"Executing LOCAL_SET with variable {name}")
    self.vars[name] = self.pop()

  def run_GLOBAL_SET(self, name):
    print(f"Executing GLOBAL_SET with variable {name}")
    self.globals[name] = self.pop()

  def run_LEI(self):
    right = self.pop()
    left = self.pop()
    print(f"Executing LEI/LEF with values {left} and {right}")
    self.push(int(left <= right))

  run_LEF = run_LEI

  def run_LTI(self):
    print(f"Executing LTI/LTF")
    right = self.pop()
    left = self.pop()
    self.push(int(left < right))

  run_LTF = run_LTI

  def run_GEI(self):
    print(f"Executing GEI/GEF")
    right = self.pop()
    left = self.pop()
    self.push(int(left >= right))

  run_GEF = run_GEI

  def run_GTI(self):
    print(f"Executing GTI/GTF")
    right = self.pop()
    left = self.pop()
    self.push(int(left > right))

  run_GTF = run_GTI

  def run_EQI(self):
    print(f"Executing EQI/EQF")
    right = self.pop()
    left = self.pop()
    self.push(int(left == right))

  run_EQF = run_EQI

  def run_NEI(self):
    print(f"Executing NEI/NEF")
    right = self.pop()
    left = self.pop()
    self.push(int(left != right))

  run_NEF = run_NEI

  def run_ANDI(self):
    self.push(self.pop() & self.pop())

  def run_ORI(self):
    self.push(self.pop() | self.pop())

  def run_GROW(self):
    self.memory.extend(b'\x00'*self.pop())
    self.push(len(self.memory))

  def run_PEEKI(self):
    addr = self.pop()
    self.push(struct.unpack("<i", self.memory[addr:addr+4])[0])

  def run_PEEKF(self):
    addr = self.pop()
    self.push(struct.unpack("<d", self.memory[addr:addr+8])[0])

  def run_PEEKB(self):
    addr = self.pop()
    self.push(self.memory[addr])

  def run_POKEI(self):
    value = self.pop()
    addr = self.pop()
    self.memory[addr:addr+4] = struct.pack("<i", value)

  def run_POKEF(self):
    value = self.pop()
    addr = self.pop()
    self.memory[addr:addr+8] = struct.pack("<d", value)

  def run_POKEB(self):
    value = self.pop()
    addr = self.pop()
    self.memory[addr] = value

  def run_JUMP(self, target):
      if target in self.line_to_index:
            self.pc = self.line_to_index[target] - 1
      else:
            raise Exception(f"Line number {target} not found")

  def run_IF(self):
    print(f"Executing IF")
    if not self.pop():
      self.pc = self.control[self.pc]

  def run_ELSE(self):
    print(f"Executing ELSE")
    self.pc = self.control[self.pc]

  def run_ENDIF(self):
    print(f"Executing ENDIF")
    pass

  def run_LOOP(self):
    print(f"Executing LOOP")
    pass

  def run_CBREAK(self):
    print(f"Executing CBREAK")
    if self.pop():
      self.pc = self.control[self.pc]

  def run_ENDLOOP(self):
    print(f"Executing ENDLOOP")
    self.pc = self.control[self.pc]

  def run_LINE(self, line):
    pass

  def run_CALL(self, name):
    print(f"Executing CALL")
    self.execute(name)

  def run_RET(self):
    print(f"Executing RET")
    self.pc = len(self.code)

def run(module):
  interpreter = Interpreter()
  has_main = False
  for func in module.functions.values():
    argnames = func.parmnames
    interpreter.add_function(func.name, argnames, func.code)

  interpreter.execute('main')
