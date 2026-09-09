from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Type
from abc import abstractmethod
from windflow_table_api import OpType, WindowKind, WindowType
from .explorer import VisitContext, VisitResult

@dataclass
class OpNode:
    """Nodo base intermedio (IR) che rappresenta un operatore nel grafo di codegen."""

    #identificativo univoco del nodo dato in fase di parsing
    node_id: str

    #operazione che rappresenta il nodo, ogni operazione ha anche una sottoclasse apposita
    op_type: OpType

    #schema di input, ottenuto dallo schema di output del parent
    schema_in: Optional[Dict[str, Any]] = None

    #schema di output, sarà l'input dell'operatore successivo
    schema_out: Optional[Dict[str, Any]] = None

    #lista di 0, 1, o 2 OpNode parents in base all'arietà dell'operatore
    parents: List[OpNode] = field(default_factory=list)

    #serializzazione JSON dell'operatore dell'api
    raw_dict: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    @abstractmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> OpNode:
        """
        Metodo che rende un'istanza della classe che lo chiama basata sul dizionario ricevuto.
        """
        pass

    @abstractmethod
    def visit(self, ctx: VisitContext) -> VisitResult:
        """
        Metodo che riempie il VisitResult in base al VisitContext e al tipo di nodo.
        """
        pass

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OpNode):
            return self.node_id == other.node_id
        return False

# -------------------------------------------------------------------------
# Sottoclassi Concrete per Operatore
# -------------------------------------------------------------------------

@dataclass
class FromOpNode(OpNode):
    """Nodo sorgente di ingestione stream (file CSV, split e timestamping)."""

    source_table_id: str = ""
    file_path: str = ""
    time_col: Optional[Dict[str, Any]] = None
    file_config: Optional[Dict[str, Any]] = None

@dataclass
class WhereOpNode(OpNode):
    """Nodo unario di filtraggio basato su un predicato booleano."""

    condition: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SelectOpNode(OpNode):
    """Nodo unario di proiezione scalare e mappatura colonne."""

    expressions: List[Dict[str, Any]] = field(default_factory=list)
    is_distinct: bool = False

@dataclass
class DistinctOpNode(OpNode):
    """Nodo unario di deduplicazione in-stream dello schema di input."""

    pass

@dataclass
class GroupByOpNode(OpNode):
    """
    Nodo stateful di raggruppamento e aggregazione (globale o con finestra).
    """

    keys: List[str] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)
    window_type: Optional[WindowType] = None
    window_kind: Optional[WindowKind] = None
    window_size: Optional[Union[int, Dict[str, Any]]] = None
    window_slide: Optional[Union[int, Dict[str, Any]]] = None

@dataclass
class JoinOpNode(OpNode):
    """Nodo binario per Window Join o Interval Join tra due rami."""

    keys: List[str] = field(default_factory=list)
    left_schema: Optional[Dict[str, Any]] = None
    right_schema: Optional[Dict[str, Any]] = None
    attachment_type: str = ""  # "INTERVAL" o "WINDOW"
    attachment_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SetOpNode(OpNode):
    """Nodo binario per operazioni insiemistiche."""

    left_schema: Optional[Dict[str, Any]] = None
    right_schema: Optional[Dict[str, Any]] = None

@dataclass
class SinkOpNode(OpNode):
    """
    Nodo foglia terminale per l'emissione dei record.
    """

    sink_target: str = ""
    output_path: Optional[str] = None

# -------------------------------------------------------------------------
# Factory con l'invocazione ai costruttori from_dict
# -------------------------------------------------------------------------

class OpNodeFactory:
    """
    Factory per istanziare nodi tipizzati a partire dal dizionario JSON.
    Chiama il metodo from_dict giusto per istanziare una delle specializzazioni di OpNode.
    """

    #dato il nome dell'operazione da fare rende il tipo da istanziare
    _REGISTRY: Dict[OpType, Type[OpNode]] = {
        OpType.FROM: FromOpNode,
        #operatori unari
        OpType.WHERE: WhereOpNode,
        OpType.SELECT: SelectOpNode,
        OpType.DISTINCT: DistinctOpNode,
        #entrambi i groupby hanno lo stesso tipo di nodo per ora
        OpType.GROUP_BY: GroupByOpNode,
        OpType.WINDOW_GROUP_BY: GroupByOpNode,
        #congiunzioni  
        OpType.JOIN_WINDOW: JoinOpNode,
        OpType.JOIN_INTERVAL: JoinOpNode,
        #operazioni insiemistiche
        OpType.UNION: SetOpNode,
        OpType.UNION_ALL: SetOpNode,
        OpType.INTERSECT: SetOpNode,
        OpType.INTERSECT_ALL: SetOpNode,
    }

    @classmethod
    def create(cls, node_id: str, op_dict: Dict[str, Any]) -> OpNode:
        raw_op_type = op_dict.get("op_type")
        if not raw_op_type:
            raise ValueError(
                f"Nodo '{node_id}' non valido: campo 'op_type' assente nel JSON."
            )

        try:
            op_type = OpType(raw_op_type)
        except ValueError:
            raise ValueError(f"OpType sconosciuto o non supportato: '{raw_op_type}'")

        #ottengo l'oggetto classe corrispondente
        target_cls = cls._REGISTRY.get(op_type)
        if not target_cls:
            raise NotImplementedError(
                f"Nessun nodo implementato per l'operatore {op_type.value}"
            )

        #delega il parsing al metodo apposito della classe
        return target_cls.from_dict(node_id=node_id, op_dict=op_dict)
