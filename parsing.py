#coding=utf-8
from util import *
from lex import Lexical
from grammar import *

from collections import namedtuple

item = namedtuple('item',['lhs','rhs_l','rhs_r','la'])
item.__repr__ = lambda self:f"{self.lhs} -> {' '.join([repr(i) for i in self.rhs_l])} . {' '.join([repr(i) for i in self.rhs_r])}  , {self.la}"

class LR1(object):
    def __init__(self,g:Grammar) -> 'LR1':
        self.g = g
        self.start = [ item(self.g.S,[],self.g.R[0].rhs,eof) ]

    def closure(self, I : [item] ) -> [item]:
        I = I[:]
        changed = True
        while changed:
            changed = False
            for it in I:
                X = it.rhs_r[0] if it.rhs_r else [ ]
                tail = it.rhs_r[1:] 
                tail = tail if tail else [eof]
                head = [i for i in self.g.first_point(tail + [it.la]) if i!=bottom]
                #self.g.sum([self.g.first_point(tail) + self.g.first_point([it.la])])
                #print("=>",head )
                for lhs,rhs in self.g.R:
                    if X == lhs:
                        for b in head:
                            value = item(lhs,[],rhs,b)
                            if value not in I:
                                I += [value]
                                changed = True
        return I

    def goto(self, I:[item], X : Vt and  Vn):
        J = [ ]
        for it in I:
            if it.rhs_r:
                if it.rhs_r[0] == X:
                    _it = item(it.lhs,it.rhs_l + [it.rhs_r[0]],it.rhs_r[1:],it.la)
                    J += [_it]
        return self.closure(J)

    def items (self) -> [item] :
        I0 = self.closure( self.start )
        C = [I0]
        changed = True
        while changed:
            changed = False
            for I in C:
                N = self.g.Vn
                V1 = self.g.Vt# + [bottom]
                V = V1 + N
                for x in V:
                    In = self.goto(I,x)
                    if In and In not in C:
                        C += [In]
                        changed = True
        return C

    def table (self, I : [item] ):
        action = [{} for i in I]
        goto   = [{} for i in I]
        target = None
        for i in range(len(I)):
            for A in I[i]:
                #print( "A =>",A,type(A.rhs_r[0]).__name__ if A.rhs_r else None)
                if A.rhs_r:
                    X = A.rhs_r[0]
                    j = self.goto(I[i],X)
                    if j:
                        idx = I.index(j)
                        if isinstance(X,Vt):
                            action[i][X] = ('shift',idx)
                        else:# isinstance(X,Vn):
                            goto[i][X] = ('shift',idx)
                elif A.rhs_l and A.rhs_r == [ ]:
                    R = rule(A.lhs,A.rhs_l)
                    idx = self.g.R.index(R)
                    if A.lhs != self.g.S:
                        action[i][A.la] = ('reduce',idx)#rule(A.lhs,A.rhs_l) )
                    else:
                        action[i][eof] = ('accept',idx)#rule(A.lhs,A.rhs_l) )
        return action,goto

    def next (self,g : ... ):
        try:
            val = next(g)
        except StopIteration:
            val = eof
        #print( "val =>",val )
        return val

    def parse (self, inp : ...,str2vt:'str -> Vt',node:['node']):
        stack = Stack()
        action,goto = self.table(self.items())
        stack.push( 0 )
        current = self.next(inp)
        ast =  AST()
        while 1:
            token,out = str2vt(current)
            state = stack.peek()
            (act,idx) = action[state][token]
            if not (out is None) and act == 'shift':
                ast.push(out)
            if act == 'shift':
                stack.push(token)
                stack.push(idx)
                current = self.next(inp)
            elif act == 'reduce':
                print( f"--------------- reduce {idx} ---------------" )
                print( "stack =>",stack )
                (lhs,rhs) = self.g.R[idx]
                length = len(rhs)
                drop = list(reversed([stack.pop() for _ in range(length * 2)]))
                #print( "drop => ",drop,ast )
                state = stack.peek()
                stack.push( lhs )
                act,val = goto[state][lhs]
                stack.push( val )
                # ast 
                print( "stack =>",stack )
                print( "ast =>",ast )
                func = node[idx]
                count = func.__code__.co_argcount
                varnames = func.__code__.co_varnames
                lctx = len(ast.ctx)
                print( "lctx,lout,count =>",lctx,count,"idx:",idx)
                valn = ast.pop(count)
                print( "valn =>",count,valn )
                ast.push(func(*valn))
                print( "ast1 =>",ast )
                print( f"---------------              ---------------" )
            elif act == 'accept':
                state = stack.pop ()
                result = stack.pop ()
                idx = 0
                print( 'ast =>',ast )
                return node[idx](*ast.ctx)
            else:
                raise ValueError(f"{act}")

__all__ = ["item","LR1"]
