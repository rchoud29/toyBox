from dataclasses import dataclass
from enum import Enum,auto
import re
class TypeKind(Enum): INT=auto(); BOOL=auto(); VOID=auto(); INT_LITERAL=auto()
@dataclass(frozen=True)
class DataType:
    kind:TypeKind; width:int=0; signed:bool=False
    def is_integer(self): return self.kind==TypeKind.INT
    @property
    def size(self): return (self.width+7)//8
    @property
    def minimum(self): return -(1<<(self.width-1)) if self.signed else 0
    @property
    def maximum(self): return (1<<(self.width-int(self.signed)))-1
    def fits(self,v): return self.minimum<=v<=self.maximum
    @property
    def name(self): return ('i' if self.signed else 'u')+str(self.width) if self.is_integer() else self.kind.name.lower()
    def __str__(self): return self.name
BOOL=DataType(TypeKind.BOOL,1); VOID=DataType(TypeKind.VOID); INT_LITERAL=DataType(TypeKind.INT_LITERAL)
def resolve_type(name):
    name=name.lower()
    if name=='bool': return BOOL
    if name=='void': return VOID
    if re.fullmatch('[ui][1-9][0-9]*',name): return DataType(TypeKind.INT,int(name[1:]),name[0]=='i')
    raise TypeError(f'Unknown type {name}')
def can_cast(src,dest): return src!=VOID and (dest.is_integer() or dest==BOOL)
def cast_value(v,t):
    if t==BOOL: return bool(v)
    if not t.is_integer(): raise TypeError('Invalid cast')
    v=int(v)&((1<<t.width)-1)
    return v-(1<<t.width) if t.signed and v>>(t.width-1) else v
