from __future__ import annotations
from enum import Enum


class DataTypes(Enum):
    """
    Rappresenta i tipi di dato supportati dalla Table API.
    Mappa i nomi logici della Table API sui reali tipi C++ nativi di WindFlow.
    """

    STRING = ("STRING")
    INT = ("INT")
    BIGINT = ("BIGINT")
    FLOAT = ("FLOAT")
    DOUBLE = ("DOUBLE")
    BOOLEAN = ("BOOLEAN")

    def __init__(self, logical_name: str):
        self.logical_name = logical_name

    def __repr__(self) -> str:
        return f"DataTypes.{self.name}"

    def is_number(self) -> bool:
        """Controlla se il tipo è numerico."""
        return self in (DataTypes.INT, DataTypes.BIGINT, DataTypes.FLOAT, DataTypes.DOUBLE)

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

        priority = {
            DataTypes.INT: 1,
            DataTypes.BIGINT: 2,
            DataTypes.FLOAT: 3,
            DataTypes.DOUBLE: 4
        }

        return max(type1, type2, key=lambda t: priority[t])
          
    