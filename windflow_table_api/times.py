from enum import Enum
from typing import Dict

class TimeUnits(str, Enum):
    """
    Rappresenta le unità di tempo supportate dalla Table API.
    """

    SECONDS = "SECONDS"
    MILLISECONDS = "MILLISECONDS"
    MINUTES = "MINUTES"
    MICROSECONDS = "MICROSECONDS"
    HOURS = "HOURS"
    DAYS = "DAYS"

    @staticmethod
    def to_microseconds(value: int, unit:str) -> int:
        """Converte un valore espresso in questa unità nei microsecondi attesi dal runtime C++."""
        mult = _TO_MICROSECONDS.get(unit)
        if not mult:
            raise KeyError(
                f"Unità di tempo {unit} sconosciuta."
            )
        return value * mult

    def __eq__(self, other):
        if isinstance(other, TimeUnits):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other

    def __hash__(self):
        return hash(self.value)

#fatto come stringa -> int così che si possa usare con i campi già serializzati
_TO_MICROSECONDS:Dict[str, int] = {
    TimeUnits.MICROSECONDS: 1,
    TimeUnits.MILLISECONDS: 1_000,
    TimeUnits.SECONDS: 1_000_000,
    TimeUnits.MINUTES: 60_000_000,
    TimeUnits.HOURS: 3_600_000_000,
    TimeUnits.DAYS: 86_400_000_000,
}

class TimeFormats(Enum):
    """
    Formati temporali di cui è supportato il parsing.
    """
    ISO8601 = "ISO8601"

class TimePolicy(Enum):
    """
    Politiche di gestione del tempo.
    - NO_POLICY: politica di default, non si possono usare finestre temporali ed intervalli, non supporta TimeCol nelle tabelle sorgente.
    - INGRESS_TIME: pone il timestamp pari all'attimo in cui la tupla viene processata, non supporta TimeCol nelle tabelle sorgente.
    - EVENT_TIME: il timestamp è ricavato tramite la TimeCol obbligatoria della tabella sorgente.
    """
    INGRESS_TIME = "INGRESS_TIME"
    EVENT_TIME = "EVENT_TIME"
    NO_POLICY = "NO_POLICY"