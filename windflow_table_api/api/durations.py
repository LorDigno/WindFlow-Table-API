from __future__ import annotations
from enum import Enum
from typing import Any, Dict

class TimeTypes(Enum):
    """
    Rappresenta le unità di tempo supportate dalla Table API.
    """

    SECONDS = "SECONDS"
    MILLISECONDS = "MILLISECONDS"
    MINUTES = "MINUTES"
    MICROSECONDS = "MICROSECONDS"
    HOURS = "HOURS"
    DAYS = "DAYS"

class Duration:
    """
    Rappresenta una durata temporale utilizzata per finestre ed intervalli.
    """

    def __init__(self, value: int, unit: TimeTypes) -> None:
        if not isinstance(value, int):
            raise TypeError(f"Il valore della durata deve essere un intero, ricevuto: {type(value)}")
        self.value = value
        self.unit = unit

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------
    @staticmethod
    def microseconds(val: int) -> Duration:
        return Duration(val, TimeTypes.MICROSECONDS)

    @staticmethod
    def milliseconds(val: int) -> Duration:
        return Duration(val, TimeTypes.MILLISECONDS)

    @staticmethod
    def seconds(val: int) -> Duration:
        return Duration(val, TimeTypes.SECONDS)

    @staticmethod
    def minutes(val: int) -> Duration:
        return Duration(val, TimeTypes.MINUTES)

    @staticmethod
    def hours(val: int) -> Duration:
        return Duration(val, TimeTypes.HOURS)

    @staticmethod
    def days(val: int) -> Duration:
        return Duration(val, TimeTypes.DAYS)

    # Supporto per il segno meno
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

    def __eq__(self, other) -> bool:
        if not isinstance(other, Duration): return False
        return (self.value == other.value) and (self.unit == other.unit)

class TimeCol:
    """
    Rappresenta una colonna da cui estrarre il timestamp nella sorgente.
    """

    def __init__(self, name: str, unit: TimeTypes):
        self.name = name
        self.unit = unit    

    def __repr__(self) -> str:
        return f"({self.name}, {self.unit.value})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit.value
        }
   