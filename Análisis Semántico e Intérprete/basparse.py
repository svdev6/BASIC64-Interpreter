from rich import print
import sly

from baslex    import Lexer
from basast    import *

class SyntaxError(Exception):
    pass

class Parser(sly.Parser):

    expected_shift_reduce = 2
    debugfile = 'parse.txt'

    tokens = Lexer.tokens

    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('left', '^'),
        ('right', UMINUS),
    )

    # Definición de programa y stmt "statement"

    @_("program stmt")
    def program(self, p):
        line, stmt = p.stmt
        p.program[line] = stmt
        return p.program

    @_("stmt")
    def program(self, p):
        line, stmt = p.stmt
        return Program({line: stmt})
    
    @_("error")
    def program(self, p):
        raise SyntaxError("Programa malformado")
    
    # Definición de comandos

    @_("INTEGER command NEWLINE")
    def stmt(self, p):
        return (p.INTEGER, p.command)
    
    @_("command")
    def command(self, p):
        return p.command

    '''
    @_("command")
    def commands(self, p):
        return [ p.command ]
    
    @_("commands ':' command")
    def commands(self, p):
        return p.commands + [ p.command ]
    '''

    @_("INTEGER error NEWLINE")
    def stmt(self, p):
        raise SyntaxError("Error en comando")
    
    @_("INTEGER NEWLINE", "NEWLINE")
    def stmt(self, p):
        raise SyntaxError("Linea Vacia")
    
    # Instrucción LET

    @_("LET variable '=' expr")
    def command(self, p):
        return Let(p.variable, p.expr)
    
    @_("LET variable '=' error")
    def command(self, p):
        raise SyntaxError("Expresión errónea en LET")

    # Instrucción READ

    @_("READ varlist")
    def command(self, p):
        return Read(p.varlist)
    
    @_("RESTORE")
    def command(self, p):
        return Restore()
    
    @_("READ error")
    def command(self, p):
        raise SyntaxError("Instrucción READ malformada")

    # Instrucción DATA

    @_("DATA mixedlist")
    def command(self, p):
        return Data(p.mixedlist)
    
    @_("DATA error")
    def command(self, p):
        raise SyntaxError("Instrucción DATA malformada")
    
    @_("mixeditem")
    def mixedlist(self, p):
        return [p.mixeditem]

    @_("mixedlist ',' mixeditem")
    def mixedlist(self, p):
        return p.mixedlist + [p.mixeditem]
    
    @_("number", "STRING")
    def mixeditem(self, p):
        return p[0]
    
    # Instrucción INPUT
    
    @_("INPUT [ STRING sep ] varlist")
    def command(self, p):
        return Input((p.STRING, p.sep), p.varlist)
    
    @_("INPUT error")
    def command(self, p):
        raise SyntaxError("Instrucción INPUT malformada")
    
    # Instrucción PRINT

    @_("PRINT plist optend")
    def command(self, p):
        return Print(p.plist + [ p.optend ])
    
    @_("PRINT")
    def command(self, p):
        return Print([])
    
    @_("sep", "empty")
    def optend(self, p):
        return p[0]

    @_("PRINT error")
    def command(self, p):
        raise SyntaxError("Instrucción PRINT malformada")
    
    # Instrucción GOTO
    
    @_("GOTO INTEGER")
    def command(self, p):
        return Goto(p.INTEGER)
    
    @_("GOTO error")
    def command(self, p):
        raise SyntaxError("Instrucción GOTO malformada")
    
    # Instrucción IF-THEN

    @_("IF relexpr THEN INTEGER")
    def command(self, p):
        return IfStatement(p.relexpr, p.INTEGER)
    
    @_("IF relexpr THEN error")
    def command(self, p):
        raise SyntaxError("Linea de código incorrecta en THEN")
    
    @_("IF error THEN INTEGER")
    def command(self, p):
        raise SyntaxError("Expresión relacional incorrecta en IF")
    
    # Instrucción FOR

    @_("FOR IDENT '=' expr TO expr optstep")
    def command(self, p):
        return For(Variable(p.IDENT), p.expr0, p.expr1, p.optstep)
    
    @_("FOR IDENT '=' error TO expr optstep")
    def command(self, p):
        raise SyntaxError("Valor inicial erróneo en la instrucción FOR")
    
    @_("FOR IDENT '=' expr TO error optstep")
    def command(self, p):
        raise SyntaxError("Valor final erróneo en la instrucción FOR")

    # Instrucción NEXT

    @_("NEXT IDENT")
    def command(self, p):
        return Next(Variable(p.IDENT))

    @_("NEXT error")
    def command(self, p):
        raise SyntaxError("Instrucción NEXT malformada")
    
    # Instrucción END
    
    @_("END")
    def command(self, p):
        return End()
    
    # Instrucción REM

    @_("REM")
    def command(self, p):
        return Remark(p.REM)

    # Instrucción STOP

    @_("STOP")
    def command(self, p):
        return Stop()
    
    # Instrucción DEF

    @_("DEF FNAME '(' IDENT ')' '=' expr")
    def command(self, p):
        return Def(p.FNAME, p.IDENT, p.expr)
    
    @_("DEF FNAME '(' IDENT ')' '=' error")
    def command(self, p):
        raise SyntaxError("Expresión incorrecta en la instrucción DEF")
    
    @_("DEF FNAME '(' error ')' '=' expr")
    def command(self, p):
        raise SyntaxError("Argumento incorrecto en la instrucción DEF")
    
    # Instrucción GOSUB

    @_("GOSUB INTEGER")
    def command(self, p):
        return GoSub(p.INTEGER)
    
    @_("GOSUB error")
    def command(self, p):
        raise SyntaxError("Instrucción GOSUB malformada")
    
    # Instrucción RETURN

    @_("RETURN")
    def command(self, p):
        return Return()
    
    # Instrucción DIM

    @_("DIM dimlist")
    def command(self, p):
        return Dim(p.dimlist)
    
    @_("DIM error")
    def command(self, p):
        raise SyntaxError("Instrucción DIM malformada")
    
    # Expresiones aritméticas

    @_("expr '+' expr",
       "expr '-' expr",
       "expr '*' expr",
       "expr '/' expr",
       "expr '^' expr")
    def expr(self, p):
        return Binary(p[1], p.expr0, p.expr1)
    
    # Definición de número, string y variable

    @_("INTEGER", "FLOAT")
    def expr(self, p):
        return Number(p[0])
    
    @_("STRING")
    def expr(self, p):
        return String(p.STRING)
    
    @_("variable")
    def expr(self, p):
        return p.variable
    
    # Instrucción BLTIN para funciones predefinidas

    @_("BLTIN '(' ')'")
    def expr(self, p):
        return Bltin(p.BLTIN)
    
    @_("BLTIN '(' exprlist ')'")
    def expr(self, p):
        return Bltin(p.BLTIN, p.exprlist)
    
    # Llamado a función
    
    @_("FNAME '(' exprlist ')'")
    def expr(self, p):
        return Call(p.FNAME, p.exprlist)
    
    # Expresiones

    @_("'(' expr ')'")
    def expr(self, p):
        return Group(p.expr)
    
    @_("expr")
    def exprlist(self, p):
        return [ p.expr ]
    
    @_("exprlist ',' expr")
    def exprlist(self, p):
        return p.exprlist + [ p.expr ]

    @_("'-' expr %prec UMINUS")
    def expr(self, p):
        return Unary(p[0], p.expr)
    
    # Expresiones relacionales

    @_("expr LT expr",
       "expr LE expr",
       "expr GT expr",
       "expr GE expr",
       "expr '=' expr",
       "expr NE expr")
    def relexpr(self, p):
        return Logical(p[1], p.expr0, p.expr1)

    # Identificadores

    @_("IDENT")
    def variable(self, p):
        return Variable(p.IDENT)
    
    @_("IDENT '(' expr ')'")
    def variable(self, p):
        return Variable(p.IDENT, p.expr)

    @_("IDENT '(' expr ',' expr ')'")
    def variable(self, p):
        return Variable(p.IDENT, p.expr0, p.expr1)

    # Salto opcional

    @_("STEP expr")
    def optstep(self, p):
        return p.expr

    # Salto opcional vacío

    @_("empty")
    def optstep(self, p):
        pass

    # Elementos para la instrucción DIM

    @_("IDENT '(' INTEGER ')'")
    def dimitem(self, p):
        return Variable(p.IDENT, Number(p.INTEGER))

    @_("IDENT '(' INTEGER ',' INTEGER ')'")
    def dimitem(self, p):
        return Variable(p.IDENT, Number(p.INTEGER0), Number(p.INTEGER1))

    @_("dimitem")
    def dimlist(self, p):
        return [ p.dimitem ]

    @_("dimlist ',' dimitem")
    def dimlist(self, p):
        p.dimlist.append(p.dimitem)
        return p.dimlist
    
    # Variables

    @_("variable")
    def varlist(self, p):
        return [ p.variable ]
    
    @_("varlist ',' variable")
    def varlist(self, p):
        return p.varlist + [ p.variable ]
    
    # Lista de números

    @_("INTEGER")
    def number(self, p):
        return Number(int(p[0]))

    @_("FLOAT")
    def number(self, p):
        return Number(float(p[0]))

    @_("'-' INTEGER %prec UMINUS", "'-' FLOAT %prec UMINUS")
    def number(self, p):
        return Number(-p[1])
    
    # Elementos para Print

    @_("pitem")
    def plist(self, p):
        return [p.pitem]

    @_("plist sep pitem")
    def plist(self, p):
        return p.plist + [ p.sep ] + p.pitem
    
    '''
    @_("STRING")
    def pitem(self, p):
        return String(p.STRING)
    '''

    @_("STRING expr")
    def pitem(self, p):
        return [ p.STRING, p.expr ]

    @_("expr")
    def pitem(self, p):
        return [ p.expr ]
    
    @_("','", "';'")
    def sep(self, p):
        return p[0]

    @_("")
    def empty(self, p):
        pass

    def error(self, p):
        lineno = p.lineno if p else 'EOF'
        value  = p.value  if p else 'EOF'
        if self.context:
            self.context.error(lineno, f"Error de sintaxis en {value}")
        else:
            print(f"Línea {lineno}: Error de sintaxis en {value}")

    def __init__(self, context = None):
        self.context = context

def test(txt):
    from basinterp import Interpreter
    l = Lexer()
    p = Parser()
    verbose = False
    try:
        prog = p.parse(l.tokenize(txt))
        "print(prog)"
        Interpreter.interpret(prog.lines, verbose = verbose)

    except SyntaxError as e:
        print(e)

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("usage: python basparse.py source")
        exit(1)

    test(open(sys.argv[1]).read())