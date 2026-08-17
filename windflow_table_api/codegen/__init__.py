"""
Sotto-package codegen: si occupa del parsing dell'AST JSON prodotto dall'API
e della generazione del codice C++ nativo per WindFlow.
"""

from .parser import OpNode, ParsedGraph, JsonParser
from .schema_gen import CppField, CppStruct, SchemaGenerator
from .expr_translator import ExpressionTranslator

__all__ = [
    "OpNode",
    "ParsedGraph",
    "JsonParser",
    "CppField",
    "CppStruct",
    "SchemaGenerator",
    "ExpressionTranslator"
]