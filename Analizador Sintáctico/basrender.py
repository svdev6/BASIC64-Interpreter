from graphviz import Digraph
from basast import *

class DotRender(Visitor):
    node_default = {
        'shape': 'box',
        'color': 'deepskyblue',
        'style': 'filled',
    }

    edge_default = {
        'arrowhead': 'none'
    }

    def __init__(self):
        self.dot = Digraph('AST')
        self.dot.attr('node', **self.node_default)
        self.dot.attr('edge', **self.edge_default)
        self.seq = 0

    def __repr__(self):
        return self.dot.source

    def __str__(self):
        return self.dot.source

    @classmethod
    def render(cls, n: Node):
        dot = cls()
        n.accept(dot)
        return dot.dot

    def name(self):
        self.seq += 1
        return f'n{self.seq:02d}'

    def visit(self, n):
        method_name = f'visit_{type(n).__name__}'
        visit_method = getattr(self, method_name, self.generic_visit)
        return visit_method(n)

    def generic_visit(self, n):
        name = self.name()
        self.dot.node(name, label=str(n))
        return name

    def visit_Program(self, n: Program):
        name = self.name()
        self.dot.node(name, label=f'Program')
        for stmt in n.lines.values():
            self.dot.edge(name, stmt.accept(self))
        return name

    def visit_Command(self, n: Command):
        name = self.name()
        self.dot.node(name, label=f'Command\nlineno: {n.lineno}')
        self.dot.edge(name, n.stmt.accept(self))
        return name

    def visit_Remark(self, n: Remark):
        name = self.name()
        self.dot.node(name, label=f'Remark:{n.rem[3:]}')
        return name

    def visit_For(self, n: For):
        name = self.name()
        self.dot.node(name, label='For')
        self.dot.edge(name, n.ident.accept(self), label='ident')
        self.dot.edge(name, n.low.accept(self), label='low')
        self.dot.edge(name, n.top.accept(self), label='top')
        if n.step:
            self.dot.edge(name, n.step.accept(self), label='step')
        return name

    def visit_Let(self, n: Let):
        name = self.name()
        self.dot.node(name, label='Let')
        self.dot.edge(name, n.var.accept(self), label='var')
        self.dot.edge(name, n.expr.accept(self), label='expr')
        return name

    def visit_Next(self, n: Next):
        name = self.name()
        self.dot.node(name, label='Next')
        self.dot.edge(name, n.ident.accept(self))
        return name

    def visit_Variable(self, n: Variable):
        name = self.name()
        self.dot.node(name, label=f'Variable')
        return name

    def visit_Number(self, n: Number):
        name = self.name()
        self.dot.node(name, label=f'Number\nvalue {n.value}')
        return name

    def visit_End(self, n: End):
        name = self.name()
        self.dot.node(name, label='END')
        return name

    def visit_IfStatement(self, n: IfStatement):
        name = self.name()
        self.dot.node(name, label='If')
        self.dot.edge(name, n.relexpr.accept(self), label='relexpr')
        return name

    def visit_Goto(self, n: Goto):
        name = self.name()
        self.dot.node(name, label='Goto')
        return name

    def visit_Data(self, n: Data):
        name = self.name()
        self.dot.node(name, label='Data')
        for num in n.numlist:
            self.dot.edge(name, num.accept(self))
        return name

    def visit_Read(self, n: Read):
        name = self.name()
        self.dot.node(name, label='Read')
        for var in n.varlist:
            self.dot.edge(name, var.accept(self))
        return name

    def visit_Stop(self, n: Stop):
        name = self.name()
        self.dot.node(name, label='STOP')
        return name
    
    def visit_Def(self, n: Def):
        name = self.name()
        self.dot.node(name, label='Def')
        self.dot.edge(name, n.fn.accept(self), label='fname')
        self.dot.edge(name, n.ident.accept(self), label='ident')
        self.dot.edge(name, n.expr.accept(self), label='expr')
        return name

    def visit_GoSub(self, n: GoSub):
        name = self.name()
        self.dot.node(name, label=f'Gosub\nlineno {n.integer}')
        return name

    def visit_Dim(self, n: Dim):
        name = self.name()
        self.dot.node(name, label='Dim')
        for var in n.dimlist:
            self.dot.edge(name, var.accept(self))
        return name

    def visit_Print(self, n: Print):
        name = self.name()
        self.dot.node(name, label='Print')
        if isinstance(n.plist, String):  # Verifica si plist es un objeto String
            self.dot.edge(name, n.plist.accept(self))  # Llama a accept directamente en el objeto String
        elif isinstance(n.plist, Variable): # Verifica si plist es un objeto Variable
            self.dot.edge(name, n.plist.accept(self)) # Llama a accept directamente en el objeto Variable
        else:
            for expr in n.plist:  # Itera sobre una lista de expresiones
                self.dot.edge(name, expr.accept(self))
        if n.optend:
            self.dot.edge(name, n.optend.accept(self), label='optend')
        return name


    def visit_Binary(self, n: Binary):
        name = self.name()
        self.dot.node(name, label=f'Binary\nop {n.op}')
        self.dot.edge(name, n.left.accept(self), label='left')
        self.dot.edge(name, n.right.accept(self), label='right')
        return name

    def visit_Logical(self, n: Logical):
        name = self.name()
        self.dot.node(name, label='Logical')
        return name

    def visit_Unary(self, n: Unary):
        name = self.name()
        self.dot.node(name, label='Unary')
        self.dot.edge(name, n.op.accept(self), label='op')
        self.dot.edge(name, n.expr.accept(self), label='expr')
        return name

    def visit_Literal(self, n: Literal):
        name = self.name()
        self.dot.node(name, label='Literal')
        return name

    def visit_String(self, n: String):
        name = self.name()
        self.dot.node(name, label=f'String\nvalue: {n.value}')
        return name

    def visit_Array(self, n: Array):
        name = self.name()
        self.dot.node(name, label='Array')
        return name