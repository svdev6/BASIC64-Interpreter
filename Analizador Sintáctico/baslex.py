# coding: utf-8
import sly
import re

class Lexer(sly.Lexer):

	reflags = re.IGNORECASE

	tokens = {
		# Keywords
		LET, READ, DATA, PRINT, GOTO, IF,
		THEN, FOR, NEXT, TO, STEP, END,
		STOP, DEF, GOSUB, DIM, REM, RETURN, BLTIN, INPUT,

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
	ignore = r' \t\r'

	# Expresiones regulares
	@_(r'REM .*')
	def REM(self, t):
		t.value = t.value[4:]
		return t

	LET    = r'LET|let'
	READ   = r'READ|read'
	DATA   = r'DATA|data'
	PRINT  = r'PRINT|print'
	GOTO   = r'GOTO|goto'
	IF     = r'IF|if'
	THEN   = r'THEN|then'
	FOR    = r'FOR|for'
	NEXT   = r'NEXT|next'
	TO     = r'TO|to'
	STEP   = r'STEP|step'
	END    = r'END|end'
	STOP   = r'STOP|stop'
	DEF    = r'DEF|def'
	GOSUB  = r'GOSUB|gosub'
	DIM    = r'DIM|dim'
	RETURN = r'RETURN|return'
	INPUT = r'INPUT|input'

	BLTIN = r'SIN|COS|TAN|ATN|EXP|ABS|LOG|SQR|RND|INT|TAB|DEG|PI|TIME|sin|cos|tan|atn|exp|abs|log|sqr|rnd|int|tab|deg|pi|time'

	FNAME = r'FN ?[A-Z]|fn ?[a-z]'
	IDENT = r'[A-Z]\d?\$?|[a-z]\d?\$'

	LE = r'<='
	LT = r'<'
	GE = r'>='
	GT = r'>'
	NE = r'<>'

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