from typing import Dict
from enum import Enum

#mappa dei tipi logici coi rispettivi tipi C++
TYPE_MAP: Dict[str, str] = {
        "INT": "int32_t",
        "BIGINT": "int64_t",
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
        "%": "%",
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
    
