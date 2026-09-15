from typing import Dict, Any, Tuple, Callable, Union
from enum import Enum
from ..datatypes import TYPE_TRANSLATION, DataTypes
from ..object_names import AggFuncType

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

#registro per le funzioni di traduzione dei letterali
#per ora delle lambda ma si potranno fare dei metodi appositi più corposi
LITERAL_FORMATTERS: Dict[DataTypes, Callable[[Any], str]] = {
    DataTypes.BOOLEAN: lambda val: "true" if val else "false",
    DataTypes.STRING: lambda val: f'std::string("{val}")',
    DataTypes.INT: lambda val: str(int(val)),
    DataTypes.BIGINT: lambda val: f"{int(val)}LL",
    DataTypes.UBIGINT: lambda val: f"{int(val)}ULL",
    DataTypes.FLOAT: lambda val: f"{float(val)}f",
    DataTypes.DOUBLE: lambda val: str(float(val)),
}

#handler per i valori di default delle aggregazioni

def _default_sum(dtype: DataTypes, cpp_type: str) -> str:
    if not dtype.is_number():
        raise TypeError(f"L'aggregazione SUM non è applicabile a un tipo non numerico: {dtype.value}")
    return "0.0" if dtype in (DataTypes.FLOAT, DataTypes.DOUBLE) else "0"

def _default_max(dtype: DataTypes, cpp_type: str) -> str:
    if dtype.is_number():
        return f"std::numeric_limits<{cpp_type}>::lowest()"
    raise TypeError(f"MAX non supportata per il tipo: {dtype.value}")

def _default_min(dtype: DataTypes, cpp_type: str) -> str:
    if dtype.is_number():
        return f"std::numeric_limits<{cpp_type}>::max()"
    raise TypeError(f"MIN non supportata per il tipo: {dtype.value}")

#tabella di dispatch per i default
_AGGREGATE_DEFAULT_DISPATCH: Dict[
    AggFuncType, Callable[[DataTypes, str], str]
] = {
    AggFuncType.COUNT: lambda dtype, cpp_type: "0",
    AggFuncType.AVG: lambda dtype, cpp_type: "0.0",
    AggFuncType.SUM: _default_sum,
    AggFuncType.MAX: _default_max,
    AggFuncType.MIN: _default_min,
}

#entry-point per i default delle aggregazioni
def get_aggregate_default(
    func_type: Union[str, AggFuncType], json_type: Union[str, DataTypes]
) -> str:
    """
    Restituisce la stringa del valore di default C++ per un dato aggregato.
    Normalizza le stringhe in Enum e delega alla tabella di dispatch.
    """
    try:
        agg_func = AggFuncType(func_type) if isinstance(func_type, str) else func_type
    except ValueError:
        raise ValueError(f"Funzione di aggregazione sconosciuta o non supportata: '{func_type}'")

    try:
        dtype = DataTypes(json_type) if isinstance(json_type, str) else json_type
    except ValueError:
        raise ValueError(f"Tipo di dato sconosciuto o non supportato: '{json_type}'")

    handler = _AGGREGATE_DEFAULT_DISPATCH.get(agg_func)
    if not handler:
        raise NotImplementedError(f"Nessun handler di default registrato per: {agg_func.value}")

    cpp_type = TYPE_TRANSLATION[dtype]
    return handler(dtype, cpp_type)
