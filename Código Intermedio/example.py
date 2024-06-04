from basparse import Parser  # Assuming you have a parser module
from baslex import Lexer
from ir_generator import IRGenerator
from basinterpir import Interpreter


def main():
    parser = Parser()
    code = """
    5 DIM A(50,15)
    10 FOR I = 1 TO 50
    20 FOR J = 1 TO 15
    30   LET A(I,J) = I + J
    35 REM  PRINT I,J, A(I,J)
    40 NEXT J
    50 NEXT I
    100 FOR I = 1 TO 50
    110 FOR J = 1 TO 15
    120   PRINT A(I,J),
    130 NEXT J
    140 PRINT 
    150 NEXT I
    999 END
    
    """

    lexer = Lexer()

    tok = lexer.tokenize(code)
    ast = parser.parse(tok)

    ir_gen = IRGenerator()
    ir_code = ir_gen.generate(ast)

    interpreter = Interpreter()

    interpreter.add_function('main', [], ir_code)
    interpreter.execute('main')

if __name__ == "__main__":
    main()