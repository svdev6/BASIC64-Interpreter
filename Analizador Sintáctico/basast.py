from dataclasses import dataclass, field
from multimethod import multimeta
from typing import List, Dict, Optional

# ---------------------------------------------------------------------
# Definicion Estructura del AST
# ---------------------------------------------------------------------
class Visitor(metaclass=multimeta):
    pass

@dataclass
class Node:
    def accept(self, v:Visitor, *args, **kwargs):
        return v.visit(self, *args, **kwargs)

@dataclass
class Statement(Node):
    pass

@dataclass
class Command(Statement):
    lineno : int
    stmt   : Statement

@dataclass
class Expression(Node):
    pass

# --- Statement
@dataclass
class Program(Statement):
    lines: Dict[int, Statement]

    def __setitem__(self, key, value):
        self.lines[key] = value

@dataclass
class Read(Statement):
    varlist : List[Expression]

@dataclass
class Let(Statement):
    var : Expression
    expr: Expression

@dataclass
class Print(Statement):
    plist: List[Expression]
    optend: str = None

@dataclass
class Input(Statement):
    label: str
    vlist: List[Expression]


@dataclass
class For(Statement):
    ident : Expression
    low   : Expression
    top   : Expression
    step  : Expression = None

@dataclass
class Next(Statement):
    ident : Expression

@dataclass
class Remark(Statement):
    rem : str

@dataclass
class End(Statement):
    pass

@dataclass
class Stop(Statement):
    pass

# --- Expression

@dataclass
class Unary(Expression):
    op   : str
    expr : Expression

@dataclass
class Binary(Expression):
    op   : str
    left : Expression
    right: Expression

@dataclass
class Logical(Binary):
    pass

@dataclass
class Variable(Expression):
    var  : str
    dim1 : Optional[Expression] = None
    dim2 : Optional[Expression] = None

@dataclass
class Bltin(Expression):
    name : str
    expr : Expression

@dataclass
class Literal(Expression):
    pass

@dataclass
class String(Literal):
    value : str
    expr  : Expression = None

@dataclass
class Number(Literal):
    value : int | float

# Corrección del nombre de la clase If a IfStatement
@dataclass
class IfStatement(Statement):
    relexpr: Expression
    lineno: int

@dataclass
class Goto(Statement):
    lineno : int

@dataclass
class Data(Statement):
    numlist : List[Expression]

@dataclass
class Stop(Statement):
    pass

@dataclass
class GoSub(Statement):
    lineno : int

@dataclass
class Dim(Statement):
    dimlist : List[Expression]

@dataclass
class Def(Statement):
    fn: str
    ident: str
    expr: Expression

@dataclass
class Call(Statement):
    name : str
    expr: Expression = None

@dataclass
class Return(Statement):
    pass

@dataclass
class Group(Statement):
    expr: Expression
