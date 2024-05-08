# coding: utf-8
import sly
import re

class Lexer(sly.Lexer):

	reflags = re.IGNORECASE

	tokens = {
		# Keywords
		LET, READ, DATA, PRINT, GOTO, IF,
		THEN, FOR, NEXT, TO, STEP, END,
		STOP, DEF, GOSUB, DIM, REM, RETURN, BLTIN, INPUT, RESTORE,

		# Operadores de relacion
		LT, LE, GT, GE, NE,

		# Identificadores
		IDENT, FNAME,

		# Constantes
		INTEGER, FLOAT, STRING,
		NEWLINE,
	}

	# Literales
	literals = '+-*/^=():,;'

	# Ignorar
	ignore = ' \t\r'

	# Expresiones regulares
	@_(r'REM( .*)?')
	def REM(self, t):
		t.value = t.value[4:] if len(t.value) > 3 else ''
		return t

	LET    = r'LET'
	READ   = r'READ'
	DATA   = r'DATA'
	PRINT  = r'PRINT'
	GOTO   = r'GOTO'
	IF     = r'IF'
	THEN   = r'THEN'
	FOR    = r'FOR'
	NEXT   = r'NEXT'
	TO     = r'TO'
	STEP   = r'STEP'
	END    = r'END'
	STOP   = r'STOP'
	DEF    = r'DEF'
	GOSUB  = r'GOSUB'
	DIM    = r'DIM'
	RETURN = r'RETURN'
	INPUT = r'INPUT'
	RESTORE =r'RESTORE'

	BLTIN = r'SIN|COS|TAN|ATN|EXP|ABS|LOG|SQR|RND|INT|TAB|DEG|PI|TIME|LEN|LEFT\$|MID\$|RIGHT\$|CHR\$'

	FNAME = r'FN ?[A-Z]'
	IDENT = r'[A-Z][A-Z0-9]*\$?'

	NE = r'<>'
	LE = r'<='
	LT = r'<'
	GE = r'>='
	GT = r'>'


	@_(r'((\d*\.\d+)(E[\+-]?\d+)?|([1-9]\d*E[\+-]?\d+))')
	def FLOAT(self, t):
		t.value = float(t.value)
		return t

	@_(r'\d+')
	def INTEGER(self, t):
		t.value = int(t.value)
		return t

	@_(r'"[^"]*"?')
	def STRING(self, t):
		t.value = t.value[1:-1]
		return t

	@_(r'\n+')
	def NEWLINE(self, t):
		self.lineno += 1
		t.value = t.value.replace('\n', '\'n')
		return t

	def error(self, t):
		print('Caracter ilegal: %s' % t.value[0], t.lineno)
		self.index += 1

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 2:
		print('Uso: baslex.py filename')
		sys.exit(1)

	data = open(sys.argv[1]).read()

	lex = Lexer()
	for tok in lex.tokenize(data):
		print(tok)