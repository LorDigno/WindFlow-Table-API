from enum import Enum

class TimeUnits(Enum):
    """
    Rappresenta le unità di tempo supportate dalla Table API.
    """

    SECONDS = "SECONDS"
    MILLISECONDS = "MILLISECONDS"
    MINUTES = "MINUTES"
    MICROSECONDS = "MICROSECONDS"
    HOURS = "HOURS"
    DAYS = "DAYS"

    def to_microseconds(self, value: int) -> int:
        """Converte un valore espresso in questa unità nei microsecondi attesi dal runtime C++[cite: 2, 7]."""
        return value * _TO_MICROSECONDS[self.value]

_TO_MICROSECONDS = {
      "MICROSECONDS": 1,
      "MILLISECONDS": 1_000,
      "SECONDS": 1_000_000,
      "MINUTES": 60_000_000,
      "HOURS": 3_600_000_000,
      "DAYS": 86_400_000_000,
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