"""
Modulo core dell'API Python di WindFlow Table API.
Espone la totalità dei tipi di dato, schemi, espressioni, durate, finestre, operatori e l'ambiente.
"""

# -------------------------------------------------------------------------
# Tipi di dato e Schema
# -------------------------------------------------------------------------
from .datatypes import DataTypes
from .schema import Field, Schema, SchemaBuilder

# -------------------------------------------------------------------------
# Espressioni e Funzioni Helper (expressions.py)
# -------------------------------------------------------------------------
from .expressions import (
    Expression,
    UnaryOpExpression,
    BinaryOpExpression,
    ColRefExpression,
    LiteralExpression,
    col,
    lit,
    # Funzioni di aggregazione
    sum,
    avg,
    min,
    max,
    count,
    #helper per operatori
    neg
)

# -------------------------------------------------------------------------
# Durate e Riferimenti Temporali (durations.py)
# -------------------------------------------------------------------------
from .durations import (
    Duration,
    TimeCol,
    TimeTypes,
    TimeFormats
)

# -------------------------------------------------------------------------
# Finestre Temporali e Intervalli (windows.py)
# -------------------------------------------------------------------------
from .windows import (
    Window,
    WindowType,
    Interval,
)

# -------------------------------------------------------------------------
# Operatori Logici (operators.py)
# -------------------------------------------------------------------------
from .operators import (
    Operator,
    UnaryOperator,
    BinaryOperator,
    WhereOp,
    SelectOp,
    DistinctOp,
    GroupByOp,
    JoinOp,
    SetOp,
    SetOpType,
    TableRefOp,
)

# -------------------------------------------------------------------------
# Drafting, Table, Environment e File
# -------------------------------------------------------------------------
from .draft import Draft
from .table import Table, Query
from .table_env import TableEnvironment, TimePolicy
from .file_config import FileFormat, InputFileConfiguration

__all__ = [
    # Data Types & Schema
    "DataTypes",
    "Field",
    "Schema",
    "SchemaBuilder",
    # Expressions & AST Nodes
    "Expression",
    "UnaryOpExpression",
    "BinaryOpExpression",
    "LiteralExpression",
    "ColRefExpression",
    "col",
    "lit",
    # Aggregations
    "sum",
    "avg",
    "min",
    "max",
    "count",
    # Expr.Operators Helpers
    "neg",
    # Durations & Time
    "Duration",
    "TimeCol",
    "TimeTypes",
    "TimeFormats",
    # Windows
    "Window",
    "WindowType",
    "Interval",
    # Operators
    "Operator",
    "UnaryOperator",
    "BinaryOperator",
    "WhereOp",
    "SelectOp",
    "DistinctOp",
    "GroupByOp",
    "JoinOp",
    "SetOp",
    "SetOpType",
    "TableRefOp",
    # DSL & Environment
    "Draft",
    "Table",
    "Query",
    "TableEnvironment",
    "TimePolicy",
    "FileFormat",
    "InputFileConfiguration"
]