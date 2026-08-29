"""
Sotto-package codegen: si occupa del parsing dell'AST JSON prodotto dall'API
e della generazione del codice C++ nativo per WindFlow.
"""

from .parser import OpNode, ParsedGraph, JsonParser
from .schema_gen import CppField, CppStruct, SchemaGenerator
from .expr_translator import ExpressionTranslator
from .utility import (
    TYPE_MAP, 
    OPERATOR_MAP, 
    get_aggregate_default, 
    parse_window, 
    parse_duration_to_microseconds, 
    parse_interval
)
from .lambda_gen import LambdaGenerator
from .explorer import GraphExplorer
from .code_generator import main

__all__ = [
    "OpNode",
    "ParsedGraph",
    "JsonParser",
    "CppField",
    "CppStruct",
    "SchemaGenerator",
    "ExpressionTranslator",
    "TYPE_MAP",
    "OPERATOR_MAP",
    "LambdaGenerator",
    "GraphExplorer",
    "get_aggregate_default",
    "parse_window",
    "parse_duration_to_microseconds",
    "parse_interval",
    "code_generator"
]