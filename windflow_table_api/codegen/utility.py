from typing import Dict
from enum import Enum

#mappa dei tipi logici coi rispettivi tipi C++
TYPE_MAP: Dict[str, str] = {
        "INT": "int32_t",
        "BIGINT": "int64_t",
        "UBIGINT": "uint64_t",         #usato per i window id, non esposto all'utente
        "FLOAT": "float",
        "DOUBLE": "double",
        "STRING": "std::string",
        "BOOLEAN": "bool",
    }

#mappa degli operatori logici/aritmetici tra JSON e C++
OPERATOR_MAP: Dict[str, str] = {
        # Logici
        "&&": "&&",
        "||": "||",
        "and": "&&",
        "or": "||",
        "!": "!",
        "not": "!",
        "~": "!",
        # Confronto
        "==": "==",
        "!=": "!=",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
        # Aritmetici
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "/",
    }

class OP_TYPE(Enum):
    SELECT = "SELECT",
    FROM = "FROM",
    TAB_REF = "TAB_REF",
    WHERE = "WHERE",
    GROUP_BY = "GROUP_BY"
    WINDOW_GROUP_BY = "WINDOW_GROUP_BY",
    DISTINCT = "DISTINCT"
    JOIN_INNER = "JOIN_INNER"
    JOIN_INTERVAL = "JOIN_INTERVAL"
    JOIN_WINDOW = "JOIN_WINDOW"
    UNION = "UNION"
    UNION_ALL = "UNION_ALL"
    INTERSECT = "INTERSECT"
    INTERSECT_ALL = "INTERSECT_ALL"

def get_aggregate_default(func_type: str, json_type: str) -> str:
    """
    Restituisce la stringa del valore di default C++ per un dato aggregato.
    """
    
    cpp_type = TYPE_MAP[json_type]

    if func_type == "SUM":
        if json_type in ("DOUBLE", "FLOAT"):
            return "0.0"
        return "0"

    elif func_type == "AVG":
        return "0.0"

    elif func_type == "COUNT":
        return "0"

    elif func_type == "MAX":
        return f"std::numeric_limits<{cpp_type}>::lowest()"

    elif func_type == "MIN":
        return f"std::numeric_limits<{cpp_type}>::max()"

    else:
        raise ValueError(f"Funzione di aggregazione sconosciuta: {func_type}")    