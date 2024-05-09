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
        self.dot.node(name, label=f'Remark:{n.rem}')
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
        if not n.dim1 and not n.dim2:
            self.dot.edge(name, n.var, label='var')
        elif n.dim1 and not n.dim2:
            self.dot.edge(name, n.var, label='var')
            self.dot.edge(name, n.dim1.accept(self), label='dim1')
        elif n.dim1 and n.dim1:
            self.dot.edge(name, n.var, label='var')
            self.dot.edge(name, n.dim1.accept(self), label='dim1')
            self.dot.edge(name, n.dim2.accept(self), label='dim2')
        return name

    def visit_Number(self, n: Number):
        name = self.name()
        self.dot.node(name, label=f'Number\nvalue {n.value}')
        return name

    def visit_End(self, n: End):
        name = self.name()
        self.dot.node(name, label='End')
        return name

    def visit_IfStatement(self, n: IfStatement):
        name = self.name()
        self.dot.node(name, label='If')
        self.dot.edge(name, n.relexpr.accept(self), label='relexpr')
        self.dot.edge(name, str(n.lineno), label='lineno')
        return name

    def visit_Goto(self, n: Goto):
        name = self.name()
        self.dot.node(name, label='Goto')
        self.dot.edge(name, str(n.lineno), label='lineno')
        return name

    def visit_Data(self, n: Data):
        name = self.name()
        self.dot.node(name, label='Data')
        for data in n.mixedlist:
            self.dot.edge(name, data.accept(self))
        return name

    def visit_Read(self, n: Read):
        name = self.name()
        self.dot.node(name, label='Read')
        for var in n.varlist:
            self.dot.edge(name, var.accept(self))
        return name

    def visit_Stop(self, n: Stop):
        name = self.name()
        self.dot.node(name, label='Stop')
        return name
    
    def visit_Def(self, n: Def):
        name = self.name()
        self.dot.node(name, label='Def')
        if isinstance(n.fn, str):
            self.dot.edge(name, n.fn, label='fname')
        if isinstance(n.ident, str):
            self.dot.edge(name, n.ident, label='ident')
        self.dot.edge(name, n.expr.accept(self), label='expr')
        return name

    def visit_GoSub(self, n: GoSub):
        name = self.name()
        self.dot.node(name, label='Gosub')
        self.dot.edge(name, str(n.lineno), label='lineno')
        return name
    
    def visit_Return(self, n: Return):
        name = self.name()
        self.dot.node(name, label='Return')
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
        clean_plist = [item for item in n.plist if hasattr(item, 'accept')]
        for pitem in n.plist:
            if isinstance(pitem, list):
                for item in pitem:
                    self.dot.edge(name, item.accept(self), label='pitem')
            elif isinstance(pitem, str):
                self.dot.edge(name, pitem, label='pitem')
        for expr in clean_plist:
                self.dot.edge(name, expr.accept(self), label='expr')
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
        self.dot.edge(name, n.op, label='op')
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

    def visit_Group(self, n: Group):
        name = self.name()
        self.dot.node(name, label='Group')
        self.dot.edge(name, n.expr.accept(self), label='expr')
        return name
    
    def visit_Bltin(self, n: Bltin):
        name = self.name()  # Get a unique node name
        self.dot.node(name, label=f'Bltin\nname: {n.name}')  # Create a node for the built-in function
        # If there's a list of expressions, create edges to each
        if n.expr:
            for expr in n.expr:
                self.dot.edge(name, expr.accept(self), label='expr')
        return name
    
    def visit_Input(self, n: Input):
        name = self.name()  # Get a unique node name
        self.dot.node(name, label=f'Input\nlabel: {n.label}')  # Create a node for the input label
        # Connect to each variable in the input list
        for var in n.vlist:
            self.dot.edge(name, var.accept(self), label='var')
        return name
    
    def visit_Call(self, n: Call):
        name = self.name()  # Get a unique node name
        self.dot.node(name, label=f'Call\nname: {n.name}')  # Create a node for the function call
        # Connect to each argument in the expression list
        if n.expr:
            for expr in n.expr:
                self.dot.edge(name, expr.accept(self), label='arg')
        return name
    
    def visit_Restore(self, n: Restore):
        name = self.name()
        self.dot.node(name, label='RESTORE')
        return name


