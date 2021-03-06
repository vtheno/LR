#coding=utf-8
from lr1p.util import *
from lr1p.lex import Lexical
from lr1p.grammar import *

from collections import namedtuple
import threading

item = namedtuple('item',['lhs','rhs_l','rhs_r','la'])
item.__repr__ = lambda self:f"{self.lhs} -> {' '.join([repr(i) for i in self.rhs_l])} . {' '.join([repr(i) for i in self.rhs_r])}  , {self.la}"

class ParseError(Exception): pass

def Filter(fn,args):
    for i in args:
        if fn(i):
            yield i

class LR1(object):
    def __init__(self,g:Grammar,lex:Lexical) -> 'LR1':
        self.g = g
        self.start = (i for i in [item(self.g.S,[],self.g.R[0].rhs,eof)])
        self.action_table = [ ]
        self.goto_table = [ ]
        self.items()
        self.table()
        self.stack = Stack()
        self.lex = lex

    def closure(self, I : [item] ) -> [item]:
        I = [*I]
        changed = True
        while changed:
            changed = False
            for it in I:
                X = it.rhs_r[0] if it.rhs_r else [ ]
                tail = it.rhs_r[1:] 
                tail = tail if tail else [eof]
                for b in self.g.first_point(tail + [it.la]):
                    if b!=bottom:
                        for lhs,rhs in self.g.R:
                            if X == lhs:
                                value = item(lhs,[],rhs,b)
                                if value not in I:
                                    I += [value]
                                    changed = True
        return I

    def goto(self, I:[item], X : 'Vt + Vn'):
        return self.closure(item(it.lhs,it.rhs_l + [it.rhs_r[0]],it.rhs_r[1:],it.la) for it in I if it.rhs_r and it.rhs_r[0] == X)
    def items (self) -> [item] :
        I0 = self.closure( self.start )
        self.C = [I0]
        self.targets = [{}]
        changed = True
        while changed:
            changed = False
            for i,I in enumerate(self.C):
                for X in self.g.V:
                    In = self.goto(I,X)
                    if In and In not in self.C:
                        self.C += [In]
                        self.targets += [{}]
                        self.targets[i][X] = i + 1#C.index(In)
                        changed = True
                    if In in self.C:
                        self.targets[i][X] = self.C.index(In)
                    

    def table_point(self,i :int):
        for A in self.C[i]:
            if A.rhs_r:
                X  = A.rhs_r[0]
                idx  = self.targets[i][X] #self.goto(I[i],X)
                if idx:
                    # idx = I.index(j)
                    # print( "=>", idx,"<=>",self.targets[i].get(X,None) )
                    if isinstance(X,Vt):
                        self.action_table[i][X] = ('shift',idx)
                    else:# isinstance(X,Vn):
                        self.goto_table[i][X] = ('shift',idx)
            elif A.rhs_l and A.rhs_r == [ ]:
                R = rule(A.lhs,A.rhs_l)
                idx = self.g.R.index(R)
                if A.lhs != self.g.S:
                    self.action_table[i][A.la] = ('reduce',idx)#rule(A.lhs,A.rhs_l) )
                else:
                    self.action_table[i][eof] = ('accept',idx)#rule(A.lhs,A.rhs_l) )

    def table (self):
        length_I = len(self.C)
        self.action_table = [{} for _ in range(length_I)]
        self.goto_table = [{} for _ in range(length_I)]
        #print( len(self.targets),length_I )
        #if length_I > 50:
        #    for i in range(length_I):
        #        threading._start_new_thread(self.table_point,(i,))
        #else:
        for i in range(length_I):
            self.table_point(i)

    def next (self,g : ... ):
        try:
            val = next(g)
        except StopIteration:
            val = eof
        #print( "val =>",val )
        return val

    def parse (self, inp : str,str2vt:'str -> Vt',node:['node']):
        self.stack.push( 0 )
        inp = self.lex.lex(inp)
        current = self.next(inp)
        ast = ASTStack()
        while 1:
            token,out = str2vt(current)
            state = self.stack.peek()
            value = self.action_table[state].get(token,None)#[token]
            if value:
                (act,idx) = value
            else:
                raise ParseError(f"""
position: {self.lex.pos}
token: {current} : {token}
input: {self.lex.inp[:self.lex.pos]} {self.lex.inp[self.lex.pos:]}""")
            if not (out is None) and act == 'shift':
                ast.push(out)
            if act == 'shift':
                self.stack.push(token)
                self.stack.push(idx)
                current = self.next(inp)
            elif act == 'reduce':
                #print( f"--------------- reduce {idx} ---------------" ) # debug
                #print( "self.stack =>",self.stack ) # debug
                (lhs,rhs) = self.g.R[idx]
                length = len(rhs)
                drop = [*reversed([self.stack.pop() for _ in range(length * 2)])]
                # list(reversed([self.stack.pop() for _ in range(length * 2)]))
                #print( "drop => ",drop,ast ) # debug
                state = self.stack.peek()
                self.stack.push( lhs )
                act,val = self.goto_table[state][lhs]
                self.stack.push( val )
                # ast 
                #print( "self.stack =>",self.stack ) # debug
                #print( "ast =>",ast ) # debug
                func = node[idx]
                count = func.__code__.co_argcount
                lctx = len(ast.ctx)
                #print( "lctx,lout,count =>",lctx,count,"idx:",idx) # debug
                valn = ast.pop(count)
                #print( "valn =>",count,valn ) # debug
                ast.push(func(*valn))
                #print( "ast1 =>",ast ) # debug
                #print( f"---------------              ---------------" ) # debug
            elif act == 'accept':
                state = self.stack.pop ()
                result = self.stack.pop ()
                idx = 0
                return node[idx](*ast.ctx)
            else:
                raise ParseError(f"""
position: {self.lex.pos}
token: {current} : {token}
input: {self.lex.inp[:self.lex.pos]} {self.lex.inp[self.lex.pos:]}""")

__all__ = ["item","LR1","ParseError"]

