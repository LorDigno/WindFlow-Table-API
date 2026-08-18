from typing import Dict

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
