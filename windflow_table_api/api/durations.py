from __future__ import annotations
from windflow_table_api import TimeUnits, TimeFormats
from enum import Enum
from typing import Any, Dict
from functools import total_ordering

@total_ordering
class Duration:
    """
    Rappresenta una durata temporale utilizzata per finestre ed intervalli.
    """

    def __init__(self, value: int, unit: TimeUnits) -> None:
        if not isinstance(value, int):
            raise TypeError(f"Il valore della durata deve essere un intero, ricevuto: {type(value)}")
        self.value = value
        self.unit = unit

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------
    @staticmethod
    def microseconds(val: int) -> Duration:
        return Duration(val, TimeUnits.MICROSECONDS)

    @staticmethod
    def milliseconds(val: int) -> Duration:
        return Duration(val, TimeUnits.MILLISECONDS)

    @staticmethod
    def seconds(val: int) -> Duration:
        return Duration(val, TimeUnits.SECONDS)

    @staticmethod
    def minutes(val: int) -> Duration:
        return Duration(val, TimeUnits.MINUTES)

    @staticmethod
    def hours(val: int) -> Duration:
        return Duration(val, TimeUnits.HOURS)

    @staticmethod
    def days(val: int) -> Duration:
        return Duration(val, TimeUnits.DAYS)

    #supporto per il segno meno
    def __neg__(self) -> Duration:
        return Duration(-self.value, self.unit)

    def to_dict(self) -> Dict[str, Any]:
        """Serializza la durata per il JSON."""
        return {
            "value": self.value,
            "unit": self.unit.value,
        }

    def __repr__(self) -> str:
        return f"{self.value}_{self.unit.value.lower()}"

    def to_microseconds(self) -> int:
        """Restituisce la durata normalizzata in microsecondi per WindFlow."""
        return TimeUnits.to_microseconds(self.value, self.unit)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return False
        return self.to_microseconds() == other.to_microseconds()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return False
        return self.to_microseconds() < other.to_microseconds()

    def __hash__(self) -> int:
        """Consente l'uso di Duration in set e chiavi di dizionari."""
        return hash(self.to_microseconds())

class TimeCol:
    """
    Rappresenta una colonna da cui estrarre il timestamp nella sorgente.
    """

    def __init__(self, name: str, format: TimeFormats):
        self.name = name
        self.format = format    

    def __repr__(self) -> str:
        return f"({self.name}, {self.format.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "format": self.format.value
        }
   