from __future__ import annotations
from enum import Enum
from typing import Dict

class DataTypes(str, Enum):
    """
    Rappresenta i tipi di dato supportati dalla Table API.
    Mappa i nomi logici della Table API sui reali tipi C++ nativi di WindFlow.
    """

    STRING = "STRING"
    INT = "INT"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOLEAN"

    #pensato a solo uso interno
    UBIGINT =  "UBIGINT"

    @property
    def cpp_type(self) -> str:
        return TYPE_TRANSLATION[self]

    def __repr__(self) -> str:
        return f"DataTypes.{self.value}"

    #rende true se è uguale al value
    def __eq__(self, other) -> bool:
        if isinstance(other, DataTypes):
            return other.value == self.value
        elif isinstance(other, str):
            return other == self.value

        return False

    #l'hash si basa sul value
    def __hash__(self) -> int:
      return hash(self.value)

    def is_number(self) -> bool:
        """Controlla se il tipo è numerico."""
        return self in _NUMBERS

    def is_bool(self) -> bool:
        """Controlla se il tipo è un booleano."""
        return self == DataTypes.BOOLEAN

    def is_string(self) -> bool:
        """Controlla se il tipo è una stringa."""
        return self == DataTypes.STRING

    @staticmethod
    def most_general_number(type1: DataTypes, type2: DataTypes) -> DataTypes:
        """
        Dati due tipi numerici calcola quale dei due comprende l'altro. (INT, FLOAT -> FLOAT)
        Il tipo BIGINT può perdere di precisione se comparato ad un FLOAT.
        """

        if (not type1.is_number()) or (not type2.is_number()):
            raise TypeError(f"I tipi {type1.value}, {type2.value} non sono comparabili come numeri.")

        return max(type1, type2, key=lambda t: _NUMERIC_PRIORITY[t])

#manca UBIGINT perché è pensato per essere usato solo all'interno dell'API
_NUMBERS = {
    DataTypes.INT, 
    DataTypes.BIGINT, 
    DataTypes.FLOAT, 
    DataTypes.DOUBLE
}
          
_NUMERIC_PRIORITY = {
    DataTypes.INT: 1,
    DataTypes.BIGINT: 2,
    DataTypes.FLOAT: 3,
    DataTypes.DOUBLE: 4,
}

TYPE_TRANSLATION: Dict[str, str] = {
    #stringhe
    DataTypes.STRING: "std::string",

    #numeri
    DataTypes.INT: "int32_t",
    DataTypes.BIGINT: "int64_t",
    DataTypes.FLOAT: "float",
    DataTypes.DOUBLE: "double",
    DataTypes.UBIGINT: "uint64_t",

    #bool
    DataTypes.BOOLEAN: "bool"
}