from enum import Enum
from typing import Dict, Callable
from abc import ABC, abstractmethod
from .datatypes import DataTypes

class ExprOp(Enum):
    def __init__(self, cpp_syntax: str):
        self.cpp_syntax = cpp_syntax

class UnExprOp(ExprOp):
    NOT = "!"

    def resolve_unary_type(self, t:DataTypes) -> DataTypes:
        target = UNARY_TYPE_RULES[self]
        return target(t)

def _resolve_unary_not(t: DataTypes) -> DataTypes:
  if not t.is_bool():
    raise TypeError(
        f"L'operatore NOT richiede un tipo booleano, ricevuto: {t.name}"
    )
  return DataTypes.BOOLEAN    

UNARY_TYPE_RULES: Dict[UnExprOp, Callable[[DataTypes], DataTypes]] = {
    UnExprOp.NOT: _resolve_unary_not,
}

class BinExprOp(ExprOp):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    AND = "&&"
    OR = "||"
    GT = ">"
    LT = "<"
    GE = ">="
    LE = "<="
    EQ = "=="
    NE = "!="

    def resolve_binary_type(self, t_left: DataTypes, t_right: DataTypes) -> DataTypes:
        target = BINARY_TYPE_RULES[self]
        return target(t_left, t_right)

def _resolve_arithmetic(t_left: DataTypes, t_right: DataTypes) -> DataTypes:
    if not (t_left.is_number() and t_right.is_number()):
        raise TypeError(f"Operazione aritmetica non valida tra {t_left} e {t_right}")
    return DataTypes.most_general_number(t_left, t_right)

def _resolve_comparison(t_left: DataTypes, t_right: DataTypes) -> DataTypes:
    if (t_left != t_right) and not (t_left.is_number() and t_right.is_number()):
        raise TypeError(f"Confronto non valido tra {t_left} e {t_right}")
    return DataTypes.BOOLEAN

def _resolve_logical(t_left: DataTypes, t_right: DataTypes) -> DataTypes:
    if not (t_left.is_bool() and t_right.is_bool()):
        raise TypeError(f"Operatore logico richiede booleani, ricevuti: {t_left}, {t_right}")
    return DataTypes.BOOLEAN

BINARY_TYPE_RULES: Dict[BinExprOp, Callable[[DataTypes, DataTypes], DataTypes]] = {
    BinExprOp.PLUS: _resolve_arithmetic,
    BinExprOp.MINUS: _resolve_arithmetic,
    BinExprOp.MULT: _resolve_arithmetic,
    BinExprOp.DIV: _resolve_arithmetic,
    BinExprOp.GT: _resolve_comparison,
    BinExprOp.LT: _resolve_comparison,
    BinExprOp.GE: _resolve_comparison,
    BinExprOp.LE: _resolve_comparison,
    BinExprOp.EQ: _resolve_comparison,
    BinExprOp.NE: _resolve_comparison,
    BinExprOp.AND: _resolve_logical,
    BinExprOp.OR: _resolve_logical,
}
