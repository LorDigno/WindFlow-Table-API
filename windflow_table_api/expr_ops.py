from enum import Enum
from typing import Dict, Callable
from abc import ABC, abstractmethod
from .datatypes import DataTypes

class ExprOp(Enum):
    name:str
    cpp_syntax:str

class UnExprOp(ExprOp):
    NOT = "!"

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

TypeResolver = Callable[[DataTypes, DataTypes], DataTypes]

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

BINARY_TYPE_RULES: Dict[str, TypeResolver] = {
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