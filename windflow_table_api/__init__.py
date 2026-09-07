"""WindFlow Table API - Python DSL e Code Generator per Streaming Analytics su WindFlow."""

__version__ = "0.2.0"

# =============================================================================
# Tipi ed Enum Condivisi (Contratti trasversali tra API, Codegen e Runtime)
# =============================================================================
from .datatypes import DataTypes
from .object_names import (
    OpType,
    AggFuncType,
    ExprType,
    WindowKind,
    WindowType,
)
from .times import (
    TimeFormats,
    TimePolicy,
    TimeUnits,
)

# =============================================================================
# DSL e Componenti Principali (Accessibili con: from windflow_table_api import ...)
# =============================================================================
from .api.durations import Duration, TimeCol
from .api.expressions import (
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
from .api.file_config import FileFormat, InputFileConfiguration, SplitSize
from .api.schema import Field, Schema, SchemaBuilder
from .api.table import Query, Table
from .api.table_env import TableEnvironment
from .api.windows import Interval, Window

# =============================================================================
# Sottomoduli Interni
# =============================================================================
from . import api
from . import codegen
from . import runtime

__all__ = [
    # Metadati
    "__version__",
    # Enum e Tipi condivisi
    "OpType",
    "ExprType",
    "AggFuncType",
    "DataTypes",
    "TimeUnits",
    "TimeFormats",
    "TimePolicy",
    "WindowType",
    "WindowKind",
    # DSL Environment & Tabelle
    "TableEnvironment",
    "Table",
    "Query",
    # Schemi
    "Schema",
    "SchemaBuilder",
    "Field",
    # Funzioni di espressione DSL
    "col",
    "lit",
    "neg",
    "sum",
    "avg",
    "min",
    "max",
    "count",
    # Espressioni AST
    "Expression",
    "ColRefExpression",
    "LiteralExpression",
    "BinaryOpExpression",
    "UnaryOpExpression",
    "AggregateExpression",
    # Finestre, Durate e Configurazione File
    "Duration",
    "TimeCol",
    "Window",
    "Interval",
    "InputFileConfiguration",
    "FileFormat",
    "SplitSize",
    # Package
    "api",
    "codegen",
    "runtime",
]