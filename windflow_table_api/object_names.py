from enum import Enum
from .types import DataTypes, TypeDescriptor
from typing import Optional, Callable, Dict

#---- OPERATORI

class OpType(str, Enum):
    """
    Rappresenta tutti i tipi di operatori supportati nella Table API di WindFlow.
    Usata trasversalmente tra api, codegen e runtime per disaccoppiare il dispatch
    dalle stringhe cablate.
    """

    #sorgenti e riferimenti
    TABLE_REF = "TAB_REF"
    FROM = "FROM"
    SINK = "SINK"

    #operatori unari semplici
    WHERE = "WHERE"
    SELECT = "SELECT"
    DISTINCT = "DISTINCT"

    #raggruppamennti
    GLOBAL_GROUP_BY = "GLOBAL_GROUP_BY"
    WINDOW_GROUP_BY = "WINDOW_GROUP_BY"

    #congiunzioni   
    JOIN_INTERVAL = "JOIN_INTERVAL"
    JOIN_WINDOW = "JOIN_WINDOW"

    #operatori insiemistici
    UNION = "UNION"
    UNION_ALL = "UNION_ALL"
    INTERSECT = "INTERSECT"
    INTERSECT_ALL = "INTERSECT_ALL"

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.value

    #comparato ad una stringa o un optype controlla il value
    def __eq__(self, other) -> bool:
        if isinstance(other, OpType):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        
        return False

    #hashing corrispondente a quello del value
    def __hash__(self) -> int:
        return hash(self.value)
       
    @property
    def is_set_op(self) -> bool:
        """Restituisce True se l'operatore appartiene alla famiglia insiemistica."""
        return self in SET_OPERATIONS

SET_OPERATIONS = frozenset({
        OpType.UNION,
        OpType.UNION_ALL,
        OpType.INTERSECT,
        OpType.INTERSECT_ALL,
    }
)

#---- ESPRESSIONI

class ExprType(str, Enum):
    """Tipi di espressione supportati nella Table API."""

    COL_REF = "COL_REF"
    LITERAL = "LITERAL"
    BINARY_OP = "BINARY_OP"
    UNARY_OP = "UNARY_OP"
    AGGREGATE = "AGGREGATE"
    CURRENT_TIMESTAMP = "CURRENT_TIMESTAMP"

#---- Aggregazioni con metodi di risoluzione dei tipi

class AggFuncType(str, Enum):
    """Funzioni di aggregazione supportate."""

    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"

    def resolve_agg_type(
        self, input_type: Optional[TypeDescriptor] = None
    ) -> TypeDescriptor:
        """
        Risolve il tipo risultante delegando la regola al registro AGG_TYPE_RULES.
        """
        target = AGG_TYPE_RULES.get(self, _resolve_fallback)
        return target(self, input_type)

def _resolve_count(func: AggFuncType, input_type: Optional[TypeDescriptor]) -> TypeDescriptor:
  #COUNT rende sempre BIGINT perché il numero di record è potenzialmente illimitato
  return DataTypes.BIGINT

def _resolve_avg(func: AggFuncType, input_type: Optional[TypeDescriptor]) -> TypeDescriptor:
  if input_type is None:
    raise ValueError(
        f"L'aggregazione {func.value} richiede un'espressione target."
    )
  if not input_type.is_number:
    raise TypeError(
        f"L'aggregazione {func.value} richiede un tipo numerico, ricevuto:"
        f" {input_type.value}"
    )
  
  #AVG rende sempre un DOUBLE
  return DataTypes.DOUBLE

def _resolve_numeric_identity(func: AggFuncType, input_type: Optional[TypeDescriptor]) -> TypeDescriptor:
  if input_type is None:
    raise ValueError(
        f"L'aggregazione {func.value} richiede un'espressione target."
    )
  if not input_type.is_number:
    raise TypeError(
        f"L'aggregazione {func.value} richiede un tipo numerico, ricevuto:"
        f" {input_type.value}"
    )
  
  #SUM, MIN, MAX conservano il tipo numerico di input
  return input_type

def _resolve_fallback(
    func: AggFuncType, input_type: Optional[TypeDescriptor]
) -> TypeDescriptor:
  raise NotImplementedError(
     f"L'aggregazione {func.value} non è supportata."
  )

AGG_TYPE_RULES: Dict[
    AggFuncType,
    Callable[[AggFuncType, Optional[TypeDescriptor]], TypeDescriptor],
] = {
    AggFuncType.COUNT: _resolve_count,
    AggFuncType.AVG: _resolve_avg,
    AggFuncType.SUM: _resolve_numeric_identity,
    AggFuncType.MIN: _resolve_numeric_identity,
    AggFuncType.MAX: _resolve_numeric_identity,
}

#---- FINESTRE ED INTERVALLI

class WindowType(str, Enum):
    """Tipologia di attachment, finestra (CB o TB) o intervallo"""

    TIME = "TIME"
    COUNT = "COUNT"

    def __eq__(self, other) -> bool:
        if isinstance(other, WindowType):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self):
        return hash(self.value)

class WindowKind(str, Enum):
    """Forma di avanzamento della finestra."""

    TUMBLE = "TUMBLE"
    SLIDING = "SLIDING"

    def __eq__(self, other) -> bool:
        if isinstance(other, WindowKind):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self):
        return hash(self.value)
    