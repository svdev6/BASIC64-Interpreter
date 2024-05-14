# bascontext.py
#
# Clase de alto nivel que contiene todo lo relacionado con el análisis/ejecución de un 
# programa en Basic.  Sirve como depósito de información sobre el programa, incluido el 
# código fuente, informes de errores, etc.

from rich      import print
from contextlib import redirect_stdout

from baslex    import Lexer
from basparse  import Parser
from basinterp import Interpreter
from basast    import *
from basrender import DotRender

class Context:
  def __init__(self):
    self.lexer  = Lexer(self)
    self.parser = Parser(self)
    self.interp = Interpreter(self)
    self.source = ''
    self.ast = None
    self.have_errors = False

  def print_tokens(self, source):
    # Tokenize the source
    tokens = list(self.lexer.tokenize(source))  # Convert to list for iteration
      # Print each token with its details
    for token in tokens:
        # You might want to customize what information to display
        print(f"Token(type={token.type}, value={token.value}, position={token.lineno}:{token.index})")

  def parse(self, source):
    self.have_errors = False
    self.source = source
    self.ast = self.parser.parse(self.lexer.tokenize(self.source))

  def print_ast(self, source, fast, style):
    self.source = source
    self.ast = self.parser.parse(self.lexer.tokenize(self.source))
    dot = DotRender.render(self.ast)
    if style == 'dot':
      with open(fast, "w") as fout:
        fout.write(str(dot))
        print(f'AST graph written to {fast}')
    elif style == 'txt':
      print(dot)

  def run(self, uppercase, array_base, slicing, go_next, trace, tabs, random_seed, fname, print_stats, write_stats, output_file):
    if not self.have_errors:
      if output_file:
        base = fname.split('.')[0]
        fprint = base + '_print.txt'
        print(f'Redirecting PRINT output to file: {fprint}')
        with open(fprint, 'w', encoding='utf-8') as fout:
          with redirect_stdout(fout):
            return self.interp.interpret(self.ast.lines, verbose=False, uppercase = uppercase, array_base = array_base, slicing = slicing, go_next = go_next, trace = trace, tabs = tabs, random_seed = random_seed, fname = fname, print_stats = print_stats, write_stats = write_stats)
      return self.interp.interpret(self.ast.lines, verbose=False, uppercase = uppercase, array_base = array_base, slicing = slicing, go_next = go_next, trace = trace, tabs = tabs, random_seed = random_seed, fname = fname, print_stats = print_stats, write_stats = write_stats)

  def find_source(self, node):
    indices = self.parser.index_position(node)
    if indices:
      return self.source[indices[0]:indices[1]]
    else:
      return f'{type(node).__name__} (ñ unavailable)'

  def error(self, position, message):
    if isinstance(position, Node):
      lineno = self.parser.line_position(position)
      (start, end) = (part_start, part_end) = self.parser.index_position(position)
      while start >= 0 and self.source[start] != '\n':
        start -=1

      start += 1
      while end < len(self.source) and self.source[end] != '\n':
        end += 1
      print()
      print(self.source[start:end])
      print(" "*(part_start - start), end='')
      print("^"*(part_end - part_start))
      print(f'{lineno}: {message}')

    else:
      print(f'{position}: {message}')
    self.have_errors = True

