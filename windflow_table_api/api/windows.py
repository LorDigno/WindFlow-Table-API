from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional, Union
from .durations import Duration

class WindowType(Enum):
    """Tipologia di finestra supportata."""

    TIME = "TIME"    
    COUNT = "COUNT"  
    #futura OVER window?

class Window:
    """
    Rappresenta la configurazione di una finestra Tumble o Sliding
    di tipo temporale o count-based.
    Sia il parametro size che slide devono essere > 0. 
    """

    def __init__(
        self,
        window_type: WindowType,
        size: Union[int, Duration],
        slide: Optional[Union[int, Duration]] = None
    ) -> None:
        
        if window_type == WindowType.TIME and not isinstance(size, Duration):
            raise TypeError("Le finestre temporali richiedono che size sia un oggetto Duration.")
        if window_type == WindowType.COUNT and not isinstance(size, int):
            raise TypeError("Le finestre count-based richiedono che size sia un int.")

        self.window_type = window_type

        self.size = size
        if ((isinstance(size, int) and size <= 0) 
            or (isinstance(size, Duration) and size.value <= 0)
            ):
            raise ValueError("Le finestre richiedono size positiva")

        self.slide = slide if slide is not None else size

        if type(self.size) is not type(self.slide):
            raise TypeError("'size' e 'slide' devono essere dello stesso tipo.")

        if ((isinstance(self.slide, int) and self.slide <= 0) 
            or (isinstance(self.slide, Duration) and self.slide.value <= 0)
            ):
            raise ValueError("Le finestre richiedono slide positiva")

    @property
    def is_tumble(self) -> bool:
        """Restituisce True se la finestra è di tipo Tumble (size == slide)."""
        return self.size == self.slide

    @property
    def is_sliding(self) -> bool:
        """Restituisce True se la finestra è di tipo Sliding."""
        return not self.is_tumble

    @staticmethod
    def createTBWindow(size: Duration, slide: Optional[Duration] = None) -> Window:
        """
        Crea una finestra temporale con le specifiche date.
        Se la dimensione di slide non è specificata viene creata una finestra Tumble. 
        """

        return Window(WindowType.TIME, size, slide)

    @staticmethod
    def createCBWindow(size: int, slide: Optional[int] = None) -> Window:
        """
        Crea una finestra count-based con le specifiche date.
        Se la dimensione di slide non è specificata viene creata una finestra Tumble. 
        """
    
        return Window(WindowType.COUNT, size, slide)

    def to_dict(self) -> Dict[str, Any]:
        """Serializza la configurazione della finestra in un dizionario per il JSON."""

        return {
            "type": "WINDOW_" + self.window_type.value,
            "kind": "TUMBLE" if self.is_tumble else "SLIDING",
            "size": str(self.size) if isinstance(self.size, int) else self.size.to_dict(),
            "slide": str(self.slide) if isinstance(self.slide, int) else self.slide.to_dict(),
        }

    def __repr__(self) -> str:
        kind = "Tumble" if self.is_tumble else "Sliding"
        return f"Window.{kind}(type={self.window_type.value}, size={self.size}, slide={self.slide})"

class Interval:
    """
    Rappresenta un intervallo temporale [lower_bound, upper_bound]
    utilizzato per configurare le Interval Join tra due stream.
    """

    def __init__(
        self,
        lower_bound: Duration,
        upper_bound: Duration
    ) -> None:

        if lower_bound.unit != upper_bound.unit:
            raise ValueError(
                f"Gli intervalli devono avere durate della stessa unità temporale."
                f"{lower_bound.unit} != {upper_bound.unit}"
            )

        if lower_bound.value >= upper_bound.value:
            raise ValueError(
                f"Gli intervalli richiedono che lower_bound strettamente minore di upper_bound."
                f"{lower_bound.value} >= {upper_bound.value}"
            )
        
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def to_dict(self) -> Dict[str, Any]:
        """Serializza l'intervallo in un dizionario per il JSON."""
        return {
            "type": "INTERVAL",
            "lower_bound": self.lower_bound.to_dict(),
            "upper_bound": self.upper_bound.to_dict()
        }

    def __repr__(self) -> str:
        return f"Interval(lower={self.lower_bound}, upper={self.upper_bound})"
    