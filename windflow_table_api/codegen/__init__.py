"""
Sotto-package codegen: si occupa del parsing dell'AST JSON prodotto dall'API
e della generazione del codice C++ nativo per WindFlow.
"""

from .operation_nodes import OpNode, OpNodeFactory
from .parser import ParsedGraph, JsonParser
from .schema_gen import CppField, CppStruct, SchemaGenerator
from .expr_translator import ExpressionTranslator
from .utility import (
    OPERATOR_MAP, 
    get_aggregate_default, 
    parse_window, 
    parse_duration_to_microseconds, 
    parse_interval
)
from .lambda_gen import LambdaGenerator
from .explorer import GraphExplorer, VisitContext, VisitResult
from .code_generator import generate_code
from .builder_generator import BuilderGenerator

__all__ = [
    "OpNode",
    "OpNodeFactory",
    "ParsedGraph",
    "JsonParser",
    "CppField",
    "CppStruct",
    "SchemaGenerator",
    "ExpressionTranslator",
    "OPERATOR_MAP",
    "LambdaGenerator",
    "BuilderGenerator",
    "GraphExplorer",
    "VisitContext",
    "VisitResult",
    "get_aggregate_default",
    "parse_window",
    "parse_duration_to_microseconds",
    "parse_interval",
    "code_generator",
    "generate_code"
]