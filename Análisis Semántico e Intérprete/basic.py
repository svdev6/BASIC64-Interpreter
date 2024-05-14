# basic.py

'''
Usage: basic.py [-h] [-a style] [-o OUT] [-l] [-D] [-p] [-I] [--sym] [-S] [-R] [-u] [-ar] [-sl] [-n] [-g] [-t] [--tabs] input

Compiler for BASIC DARTMOUTH 64

Positional arguments:
  input              BASIC program file to compile

Optional arguments:
  -h, --help                 Show this help message and exit
  -D, --debug                Generate assembly with extra information (for debugging purposes)
  -o OUT, --out OUT          File name to store generated executable
  -l, --lex                  Store output of lexer
  -a STYLE                   Generate AST graph as DOT or TXT format
  -I, --ir                   Dump the generated Intermediate representation
  --sym                      Dump the symbol table
  -S, --asm                  Store the generated assembly file
  -R, --exec                 Execute the generated program
  -v, --version              Show the version of the BASIC interpreter
  -u, --uppercase            Convert all entries to uppercase
  -ar INT, --array-base INT  Set the minimum index of the dimensional arrays (default is 1)
  -sl, --slicing             Enable string slicing (disable string arrays)
  -n, --no-run               Don't run the program after parsing
  -g, --go-next              If no branch from a GOTO instruction exists, go to the next line
  -t, --trace                Activate tracing to print line numbers during execution
  --tabs INT                 Set the number of spaces for comma-separated elements (default is 15)
  -rn INT, --random INT      Set the seed for the random number generator
  -p, --print-stats          Print statistics on program termination
  -w, --write-stats          Write statistics to a file on program termination
  -of, --output-file         Redirect PRINT output to a file
  -if, --input-file          Redirect INPUT to a file
'''

from contextlib import redirect_stdout
from rich       import print
from bascontext import Context

import argparse


def parse_args():
  cli = argparse.ArgumentParser(
    prog='basic.py',
    description='Compiler for BASIC programs'
  )

  cli.add_argument(
    '-v', '--version',
    action='version',
    version='0.4')

  fgroup = cli.add_argument_group('Formatting options')

  fgroup.add_argument(
    'input',
    type=str,
    nargs='?',
    help='BASIC program file to compile')

  mutex = fgroup.add_mutually_exclusive_group()

  mutex.add_argument(
    '-l', '--lex',
    action='store_true',
    default=False,
    help='Store output of lexer')

  mutex.add_argument(
    '-a', '--ast',
    action='store',
    dest='style',
    choices=['dot', 'txt'],
    help='Generate AST graph as DOT or TXT format')

  mutex.add_argument(
    '--sym',
    action='store_true',
    help='Dump the symbol table')
  
  cli.add_argument(
    '-u', '--uppercase',
    action='store_true',
    default=False,
    help='Convert all entries to uppercase')
  
  cli.add_argument(
    '-ar', '--array-base',
    type=int,
    default=1,
    help='Set the minimum index of the arrays (default is 1)')

  cli.add_argument(
   '-sl', '--slicing',
    action='store_true',
    default=False,
    help='Enable string slicing (disable string arrays)')

  cli.add_argument(
    '-n', '--no-run',
    action='store_true',
    default=False,
    help='Do not run the program after parsing')

  cli.add_argument(
    '-g', '--go-next',
    action='store_true',
    default=False,
    help='If no branch from a GOTO instruction exists, go to the next line')

  cli.add_argument(
    '-t', '--trace',
    action='store_true',
    default=False,
    help='Activate tracing to print line numbers during execution')

  cli.add_argument(
    '--tabs',
    type=int,
    default=15,
    help='Set the number of spaces for comma-separated elements (default is 15)')

  cli.add_argument(
    '-rn', '--random',
    type=int,
    help='Set the seed for the random number generator')

  cli.add_argument(
    '-p', '--print-stats',
    action='store_true',
    default=False,
    help='Print statistics on program termination')

  cli.add_argument(
    '-w', '--write-stats',
    action='store_true',
    default=False,
    help='Write statistics to a file on program termination')

  cli.add_argument(
    '-of', '--output-file',
    action='store_true',
    default=False,
    help='Redirect PRINT output to a file')

  cli.add_argument(
    '-if', '--input-file',
    type=str,
    help='Redirect INPUT to a file')

  return cli.parse_args()

if __name__ == '__main__':

  args = parse_args()
  context = Context()

  if args.input: fname = args.input
  
  with open(fname, encoding='utf-8') as file:
    source = file.read()

  if args.lex:
    flex = fname.split('.')[0] + '.lex'
    print(f'Printing Lexer output: {flex}')
    with open(flex, 'w', encoding='utf-8') as fout:
      with redirect_stdout(fout):
        context.print_tokens(source)

  elif args.style:
    base = fname.split('.')[0]
    fast = base + '.' + args.style
    print(f'Printing the AST graph: {fast}')
    with open(fast, 'w') as fout:
      with redirect_stdout(fout):
        context.print_ast(source, fast, args.style)

  elif args.sym:
    base = fname.split('.')[0]
    fsym = base + '_symtab.txt'
    print(f'Dumping symbol table: {fsym}')

  else:
    context.parse(source)
    if not args.no_run:
        context.run(args.uppercase, args.array_base, args.slicing, args.go_next, args.trace, args.tabs, args.random, fname, args.print_stats, args.write_stats, args.output_file, args.input_file)