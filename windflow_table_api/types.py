from enum import Enum
from typing import Dict, Union

class TypeDescriptor(Enum):
    """
    Interfaccia per i tipi supportati, comprende DataTypes e TimeFormats.
    """

    @property
    def logical_name(self) -> str:
        raise NotImplementedError

    @property
    def cpp_type(self) -> str:
        raise NotImplementedError

    @property
    def is_number(self) -> bool:
        return False

    @property
    def is_boolean(self) -> bool:
        return False

    @property
    def is_string(self) -> bool:
        return False

    @property
    def is_temporal(self) -> bool:
        return False

    #rende true se è uguale al value
    def __eq__(self, other) -> bool:
        if isinstance(other, TypeDescriptor):
            return other.logical_name == self.logical_name
        elif isinstance(other, str):
            return other == self.logical_name

        return False

    #l'hash si basa sul value
    def __hash__(self) -> int:
      return hash(self.logical_name)

    @classmethod
    def from_value(cls, val: Union[str, 'TypeDescriptor']) -> 'TypeDescriptor':
        """
        Ricostruisce l'istanza corretta (DataTypes o TimeFormats) a partire dal nome logico serializzato.
        Supporta chiamate sia dalla base (TypeDescriptor.from_value) sia dalle classi derivate (DataTypes.from_value).
        """
        #se è già un TypeDescriptor lo rende
        if isinstance(val, TypeDescriptor):
            return val

        if not isinstance(val, str):
            raise TypeError(
                f"Attesa stringa o TypeDescriptor, ricevuto: {type(val)} ({val})"
            )

        upper_val = val.upper()

        #cerca o nelle sottoclassi del typeDescriptor o nella classe chiamante che eredita il metodo
        target_classes = (
            [cls] if cls is not TypeDescriptor else cls.__subclasses__()
        )

        for subcls in target_classes:

            #rende l'enumerazione con lo stesso value
            for member in subcls:
                if str(member.value).upper() == upper_val:
                    return member

            #rende l'enumerazione con lo stesso name
            if upper_val in subcls.__members__:
                return subcls[upper_val]

        #errore, non si può istanziare una sottoclasse nota
        valid_subtypes = [c.__name__ for c in target_classes]
        raise ValueError(
            f"Tipo logico non riconosciuto: '{val}' nelle classi {valid_subtypes}"
        )

class DataTypes(TypeDescriptor):
    """
    Rappresenta i tipi di dato supportati dalla Table API.
    Mappa i nomi logici della Table API sui reali tipi C++ nativi di WindFlow.
    """

    STRING = "STRING"
    INT = "INT"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOL"
    UBIGINT =  "UBIGINT"

    @property
    def logical_name(self) -> str:
        return self.value

    @property
    def cpp_type(self) -> str:
        return DATA_TRANSLATIONS[self]

    def __repr__(self) -> str:
        return f"DataTypes.{self.logical_name}"

    @property
    def is_number(self) -> bool:
        """Controlla se il tipo è numerico."""
        return self in _NUMBERS

    @property
    def is_boolean(self) -> bool:
        """Controlla se il tipo è un booleano."""
        return self == DataTypes.BOOLEAN

    @property
    def is_string(self) -> bool:
        """Controlla se il tipo è una stringa."""
        return self == DataTypes.STRING

    @staticmethod
    def most_general_number(type1: TypeDescriptor, type2: TypeDescriptor) -> 'DataTypes':
        """
        Dati due tipi numerici calcola quale dei due comprende l'altro. (INT, FLOAT -> FLOAT)
        Il tipo BIGINT può perdere di precisione se comparato ad un FLOAT.
        """

        if (not isinstance(type1, DataTypes)) or (not isinstance(type2, DataTypes)):
             raise TypeError(f"I tipi {type1.logical_name}, {type2.logical_name} non sono comparabili come DataTypes.")

        if (not type1.is_number) or (not type2.is_number):
            raise TypeError(f"I tipi {type1.logical_name}, {type2.logical_name} non sono comparabili come numeri.")

        return max(type1, type2, key=lambda t: _NUMERIC_PRIORITY[t])

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

#tabella di conversione al cpp
DATA_TRANSLATIONS: Dict[DataTypes, str] = {
    #stringhe
    DataTypes.STRING: "std::string",

    #numeri
    DataTypes.INT: "int32_t",
    DataTypes.BIGINT: "int64_t",
    DataTypes.FLOAT: "float",
    DataTypes.DOUBLE: "double",
    DataTypes.UBIGINT: "uint64_t",

    #bool
    DataTypes.BOOLEAN: "bool",
}

class TimeFormats(TypeDescriptor):
    """
    Formati temporali di cui è supportato il parsing.
    """
    ISO8601 = "ISO8601"

    @property
    def logical_name(self) -> str:
        return self.value

    @property
    def cpp_type(self) -> str:
        return "uint64_t"

    @property
    def is_temporal(self) -> bool:
        return True

