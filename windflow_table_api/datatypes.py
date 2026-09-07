from __future__ import annotations
from enum import Enum

class DataTypes(Enum):
    """
    Rappresenta i tipi di dato supportati dalla Table API.
    Mappa i nomi logici della Table API sui reali tipi C++ nativi di WindFlow.
    """

    STRING = ("STRING", "std::string")
    INT = ("INT", "int32_t")
    BIGINT = ("BIGINT", "int64_t")
    FLOAT = ("FLOAT", "float")
    DOUBLE = ("DOUBLE", "double")
    BOOLEAN = ("BOOLEAN", "bool")

    #pensato a solo uso interno
    UBIGINT = ("UBIGINT", "uint64_t")

    def __init__(self, logical_name: str, cpp_name: str):
        self.logical_name = logical_name
        self.cpp_name = cpp_name

    def __repr__(self) -> str:
        return f"DataTypes.{self.name}"

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
            raise TypeError(f"I tipi {type1.name}, {type2.name} non sono comparabili come numeri.")

        return max(type1, type2, key=lambda t: _NUMERIC_PRIORITY[t])

#manca UBIGINT perché è pensato per essere usato solo all'interno dell'API
_NUMBERS = {
    DataTypes.INT, DataTypes.BIGINT, DataTypes.FLOAT, DataTypes.DOUBLE
}
          
_NUMERIC_PRIORITY = {
    DataTypes.INT: 1,
    DataTypes.BIGINT: 2,
    DataTypes.FLOAT: 3,
    DataTypes.DOUBLE: 4,
}