"""Sotto-package api: definisce il DSL logico, la gestione del Draft e il TableEnvironment."""

from .draft import Draft
from .durations import Duration, TimeCol
from .expressions import (
    AggregateExpression,
    BinaryOpExpression,
    ColRefExpression,
    Expression,
    LiteralExpression,
    UnaryOpExpression,
    avg,
    col,
    count,
    lit,
    max,
    min,
    neg,
    sum,
)
from .file_config import FileFormat, InputFileConfiguration, SplitSize
from .job_handle import JobHandle
from .operators import (
    BinaryOperator,
    DistinctOp,
    FromOp,
    GroupByOp,
    JoinOp,
    Operator,
    SelectOp,
    WhereOp,
    SetOp,
    TableRefOp,
    UnaryOperator,
)
from .schema import Field, Schema, SchemaBuilder
from .table import Query, Table
from .table_env import TableEnvironment
from .windows import Interval, Window

__all__ = [
    # Core
    "TableEnvironment",
    "Table",
    "Query",
    "Draft",
    "JobHandle",
    # Schema
    "Schema",
    "SchemaBuilder",
    "Field",
    # Nodi AST Operatori
    "Operator",
    "UnaryOperator",
    "BinaryOperator",
    "FromOp",
    "TableRefOp",
    "SelectOp",
    "WhereOp",
    "GroupByOp",
    "DistinctOp",
    "JoinOp",
    "SetOp",
    # Espressioni
    "Expression",
    "ColRefExpression",
    "LiteralExpression",
    "BinaryOpExpression",
    "UnaryOpExpression",
    "AggregateExpression",
    "col",
    "lit",
    "neg",
    "sum",
    "avg",
    "min",
    "max",
    "count",
    # Finestre e I/O
    "Duration",
    "TimeCol",
    "Window",
    "Interval",
    "InputFileConfiguration",
    "FileFormat",
    "SplitSize",
]