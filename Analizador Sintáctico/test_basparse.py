import unittest
from basparse import *

class TestParser(unittest.TestCase):

    def setUp(self):
        self.lexer = Lexer()
        self.parser = Parser()

    def test_valid_program(self):
        program = """
        1  REM ::: SOLVE A SYSTEM OF LINEAR EQUATIONS
        2  REM ::: A1*X1 + A2*X2 = B1
        3  REM ::: A3*X1 + A4*X2 = B2
        4  REM --------------------------------------
        10 READ A1, A2, A3, A4
        15 LET D = A1 * A4 - A3 * A2
        20 IF D = 0 THEN 65
        30 READ B1, B2
        37 LET X1 = (B1*A4 - B2*A2) / D
        42 LET X2 = (A1*B2 - A3*B1) / D
        55 PRINT X1, X2
        60 GOTO 30
        65 PRINT "NO UNIQUE SOLUTION"
        70 DATA 1, 2, 4
        80 DATA 2, -7, 5
        85 DATA 1, 3, 4, -7
        90 END
        
        """
        self.parser.parse(self.lexer.tokenize(program))

    def test_invalid_goto_statement(self):
        invalid_program = """
        10 GOTO

        """
        with self.assertRaises(Exception):
            self.parser.parse(invalid_program)

    def test_invalid_data_statement(self):
        invalid_program = """
        10 DATA 1, 2, 3
        """
        with self.assertRaises(Exception):
            self.parser.parse(invalid_program)

    def test_print_statement_with_expression(self):
        program = """
        10 LET X = 5
        20 LET Y = 10
        30 LET S = X + Y
        40 PRINT "The sum is: "S
        50 END
        
        """
        self.parser.parse(self.lexer.tokenize(program))

if __name__ == '__main__':
    unittest.main()
