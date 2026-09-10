from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Type
from abc import abstractmethod, ABC
from windflow_table_api import OpType, WindowKind, WindowType, TimeUnits, FileFormat, TimeFormats
from .schema_gen import SchemaGenerator, CppStruct, CppField
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator

#---- Classi di input e output comuni alla visita di ogni specializzazione di OpNode

@dataclass
class VisitContext:
    """Parametri passati dal chiamante al nodo durante la visita."""
    #nome della pipe corrente
    pipe: str

    #struct già deduplicati passati dai parent come input per l'operazione corrente
    parent_structs: List[CppStruct]     

    #nome di variabili pipes che convergono nel nodo binario 
    to_merge_pipes: List[str]    

    #generatori di struct/espressioni/lambda necessari
    sch_gen: SchemaGenerator
    expr_tl: ExpressionTranslator
    lambda_gen: LambdaGenerator

    #operations_counter necessario alla creazione di variabili univoche
    operations_counter: int      

@dataclass
class VisitResult:
    """Informazioni restituite dalla visita di un nodo."""
    out_struct: CppStruct

    #stringa da accumulare alla pipe corrente
    pipe_addition: str

    #stringhe ricavate da jinja per i builder ricavati dal nodo (ordinati)
    #attualmente un nodo può generare più operazioni (es intersect con map di tagging)
    emitted_builders: List[str] = field(default_factory=list)

#---- Nodi dell'AST rappresentanti le operazioni

@dataclass(kw_only=True)
class OpNode(ABC):
    """Nodo base intermedio che rappresenta un operatore nel grafo di codegen."""

    #identificativo univoco del nodo dato in fase di parsing
    node_id: str

    #operazione che rappresenta il nodo, ogni operazione ha anche una sottoclasse apposita
    op_type: OpType

    #schema di output, sarà l'input dell'operatore successivo
    schema_out: Dict[str, Any]

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

    @staticmethod
    def parse_duration(duration, op_dict) -> int:
        """
        Metodo comune a tutti i nodi usato per eseguire il parsing delle Duration serializzate in microsecondi.
        """

        value:int = duration.get("value")
        if not value:
            raise KeyError(
                f"Chiave 'value' mancante nella duration del nodo:\n{op_dict}."
            )

        unit:str = duration.get("unit")
        if not unit:
            raise KeyError(
                f"Chiave 'unit' mancante nella duration del nodo:\n{op_dict}."
            ) 

        return TimeUnits.to_microseconds(value, unit)            

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OpNode):
            return self.node_id == other.node_id
        return False

#classi per non duplicare i parsing degli attributi comuni in base all'arietà e utilizzo di finestre

@dataclass(kw_only=True)
class UnaryNode(OpNode, ABC):
    schema_in: Dict[str, Any]

    @classmethod
    def extract_unary_commons(
        cls, 
        node_id:str, 
        op_dict:Dict[str, Any]
    ) -> Dict[str, Any]:
        schema_in = op_dict.get("schema_in")
        if not schema_in:
            raise KeyError(
                f"Chiave 'schema_in' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        schema_out = op_dict.get("schema_out")
        if not schema_out:
            raise KeyError(
                f"Chiave 'schema_out' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        return {
            "node_id": node_id,
            "schema_in": schema_in,
            "schema_out": schema_out,
            "raw_dict": op_dict,
        }

@dataclass(kw_only=True)
class BinaryNode(OpNode, ABC):
    left_schema: Dict[str, Any]
    right_schema: Dict[str, Any]

    @classmethod
    def extract_binary_commons(cls, node_id: str, op_dict: Dict[str, Any]) -> Dict[str, Any]:
        #schemi delle due tabelle di input
        left_schema = op_dict.get("tab1_schema")
        if not left_schema:
            raise KeyError(
                f"Chiave 'tab1_schema' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )                

        right_schema = op_dict.get("tab2_schema")
        if not right_schema:
            raise KeyError(
                f"Chiave 'tab2_schema' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        #schema delle tabelle di output
        schema_out = op_dict.get("schema_out")
        if not schema_out:
            raise KeyError(
                f"Chiave 'schema_out' mancante nel nodo:\n{op_dict}\nPer la creazione di {OpType}."
            ) 

        return {
            "node_id": node_id,
            "left_schema": left_schema,
            "right_schema": right_schema,
            "schema_out": schema_out,
            "raw_dict": op_dict
        }

@dataclass(kw_only=True)
class WindowNode(OpNode, ABC):
    window_type: WindowType
    window_kind: WindowKind
    window_size: int
    window_slide: int

    @classmethod
    def extract_window(cls, window: Dict[str, Any], op_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae gli attributi della finestra, se temporale parsa le Duration in microsecondi.
        """
        w_type = window.get("type")
        if not w_type:
            raise KeyError(
                f"Chiave 'type' mancante nella finestra del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        kind = window.get("kind")
        if not kind:
            raise KeyError(
                f"Chiave 'kind' mancante nella finestra del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        size = window.get("size")
        if not size:
            raise KeyError(
                f"Chiave 'size' mancante nella finestra del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )
        if w_type == WindowType.TIME:
            size = OpNode.parse_duration(size, op_dict) 

        slide = window.get("slide")
        if not slide:
            raise KeyError(
                f"Chiave 'slide' mancante nella finestra del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )
        if w_type == WindowType.TIME:
            slide = OpNode.parse_duration(slide, op_dict) 

        return {
            "window_type": w_type,
            "window_kind": kind,
            "window_size": size,
            "window_slide": slide,
        }

# -------------------------------------------------------------------------
# Sottoclassi Concrete per Operatore
# -------------------------------------------------------------------------

#---- Sorgenti

@dataclass(kw_only=True)
class FromOpNode(OpNode):
    """Nodo sorgente di ingestione stream (file CSV, split e timestamping)."""

    op_type:OpType = OpType.FROM
    source_table_id:str 
    filepath:str

    #formattazione del file
    header:bool
    file_format:str
    split_size:int

    #attributi riguardanti l'event time
    time_col:Optional[str] = None
    time_format:Optional[str] = None
    delay:Optional[int] = None
    ordered:bool

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> FromOpNode:
        source_id = op_dict.get("source_id")
        if not source_id:
            raise KeyError(
                f"Chiave 'source_id' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        schema_out = op_dict.get("schema_out")
        if not schema_out:
            raise KeyError(
                f"Chiave 'schema_out' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        #ottengo la configurazione del file
        config = op_dict.get("config")
        if not config:
            raise KeyError(
                f"Chiave 'config' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        #parsing degli attributi di configurazione
        filepath = config.get("filepath")
        if not filepath:
            raise KeyError(
                f"Chiave 'filepath' mancante nella config del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        header = config.get("header")
        if header is None:
            raise KeyError(
                f"Chiave 'header' mancante nella config del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        delay = config.get("delay")
        if delay is not None:
            delay = OpNode.parse_duration(delay, op_dict)
            
        file_format = config.get("file_format")
        if file_format is None:
            raise KeyError(
                f"Chiave 'file_format' mancante nella config del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        split_size = config.get("split_size")
        if split_size is None:
            raise KeyError(
                f"Chiave 'split_size' mancante nella config del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        order = config.get("order")
        if order is None:
            raise KeyError(
                f"Chiave 'order' mancante nella config del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        #gestione della TimeCol
        time_col_name = None
        time_format = None
        time_col_dict = config.get("time_col")
        if time_col_dict is not None:
            #estraggo i campi
            time_col_name = time_col_dict.get("name")
            if time_col_name is None:
                raise KeyError(
                    f"Chiave 'name' mancante nella TimeCol del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
                )

            time_format = time_col_dict.get("format")
            if time_format is None:
                raise KeyError(
                    f"Chiave 'format' mancante nella TimeCol del nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
                )

        return cls(
            node_id= node_id,
            schema_out= schema_out,
            raw_dict= op_dict,

            source_table_id= source_id,
            filepath= filepath,

            header= header,
            file_format= file_format,
            split_size= split_size,

            time_col= time_col_name,
            time_format= time_format,
            delay= delay,
            ordered= order
        )

"""
Eventuale nodo per il Sink che attualmente non esiste
@dataclass(kw_only=True)
class SinkOpNode(OpNode):
    #""
    #Nodo foglia terminale per l'emissione dei record.
    #""

    sink_target: str = ""
    output_path: Optional[str] = None
"""

#---- Operazioni Unarie

@dataclass(kw_only=True)
class WhereOpNode(UnaryNode):
    """Nodo unario di filtraggio basato su un predicato booleano."""

    op_type:OpType = OpType.WHERE
    condition: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> WhereOpNode:
        condition = op_dict.get("condition")
        if not condition:
            raise KeyError(
                f"Chiave 'condition' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        base_args = cls.extract_unary_commons(node_id, op_dict)

        return cls(
            **base_args,
            condition= condition
        )

@dataclass(kw_only=True)
class SelectOpNode(UnaryNode):
    """Nodo unario di proiezione scalare e mappatura colonne."""

    op_type:OpType = OpType.SELECT
    expressions: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> SelectOpNode:
        expressions = op_dict.get("expressions")
        if not expressions:
            raise KeyError(
                f"Chiave 'expressions' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        base_args = cls.extract_unary_commons(node_id, op_dict)

        return cls(
            **base_args,
            expressions= expressions
        )

@dataclass(kw_only=True)
class DistinctOpNode(UnaryNode):
    """Nodo unario di deduplicazione in-stream dello schema di input."""

    op_type:OpType = OpType.DISTINCT

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> DistinctOpNode:
        base_args = cls.extract_unary_commons(node_id, op_dict)
        return cls(
            **base_args
        )

@dataclass(kw_only=True)
class GroupByOpNode(UnaryNode):
    """
    Nodo stateful di raggruppamento e aggregazione globale.
    """

    op_type:OpType = OpType.GROUP_BY 
    keys: List[str] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> GroupByOpNode:
        keys = op_dict.get("keys")
        if not keys:
            raise KeyError(
                f"Chiave 'keys' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        aggregations = op_dict.get("aggregations")
        if not aggregations:
            raise KeyError(
                f"Chiave 'aggregations' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )        

        base_args = cls.extract_unary_commons(node_id, op_dict)

        return cls(
            **base_args,
            keys= keys,
            aggregations= aggregations
        ) 

@dataclass(kw_only=True)
class WindowGroupOpNode(UnaryNode, WindowNode):
    """
    Nodo stateful di raggruppamento e aggregazione con finestra.
    """

    op_type:OpType = OpType.WINDOW_GROUP_BY

    keys: List[str] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> WindowGroupOpNode:
        keys = op_dict.get("keys")
        if not keys:
            raise KeyError(
                f"Chiave 'keys' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        aggregations = op_dict.get("aggregations")
        if not aggregations:
            raise KeyError(
                f"Chiave 'aggregations' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        #parsing dei vari attributi della finestra
        window:Dict[str, Any] = op_dict.get("window", {})
        win_args:Dict[str, Any] = cls.extract_window(window, op_dict)           

        base_args:Dict[str, Any] = cls.extract_unary_commons(node_id, op_dict)

        return cls(
            **base_args,
            **win_args,
            keys= keys,
            aggregations= aggregations,
        ) 

#---- Congiunzioni

@dataclass(kw_only=True)
class JoinNode(BinaryNode, ABC):
    """
    Classe base astratta per tutti gli operatori di join binari.
    Contiene il metodo di visita dei parametri comunia tutte le Join.
    """

    keys:List[str]

    @classmethod
    def extract_join_commons(cls, node_id:str, op_dict: Dict[str, Any]) -> Dict[str, Any]:
        keys = op_dict.get("keys")
        if not keys:
            raise KeyError(
                f"Chiave 'keys' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        base_args = cls.extract_binary_commons(node_id, op_dict)

        return {
            **base_args,
            "keys": keys
        }

@dataclass(kw_only=True)
class WindowJoinOpNode(JoinNode, WindowNode):
    """Nodo binario per Window Join tra due rami."""

    op_type:OpType = OpType.JOIN_WINDOW
    
    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> WindowJoinOpNode:
        #estrazione parametri di finestra
        window = op_dict.get("window", {})
        win_args = cls.extract_window(window, op_dict) 

        base_args = cls.extract_join_commons(node_id, op_dict)

        return cls(
            **base_args,
            **win_args
        )

@dataclass(kw_only=True)
class IntervalJoinOpNode(JoinNode):
    """
    Nodo binario per Interval Join tra due rami.
    Unico nodo che usa gli intervalli quindi per ora esegue il loro parsing internamente. 
    """

    op_type:OpType = OpType.JOIN_INTERVAL
    lower: int
    upper: int

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> IntervalJoinOpNode:
        lower = op_dict.get("lower")
        if lower is None:
            raise KeyError(
                f"Chiave 'lower' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )   
        lower = OpNode.parse_duration(lower, op_dict)

        upper = op_dict.get("upper")
        if upper is None:
            raise KeyError(
                f"Chiave 'upper' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )   
        upper = OpNode.parse_duration(upper, op_dict)   

        base_args = cls.extract_join_commons(node_id, op_dict)

        return cls(
            **base_args,
            lower= lower,
            upper= upper
        )    

#---- Operazioni Insiemistiche

@dataclass(kw_only=True)
class UnionOpNode(BinaryNode):
    """Nodo binario per operazioni di unione (topologica + distinct opzionale)."""

    is_all: bool = False

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> UnionOpNode:
        raw_op_type = op_dict.get("op_type")
        is_all = raw_op_type == OpType.UNION_ALL

        base_args = cls.extract_binary_commons(node_id, op_dict)

        return cls(
            **base_args,
            op_type=OpType.UNION_ALL if is_all else OpType.UNION,
            is_all=is_all,
        )

@dataclass(kw_only=True)
class IntersectOpNode(BinaryNode):
    """Nodo binario multistadio per intersezione di flussi (tagging + merge + functor stateful)."""

    is_all: bool = False

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> IntersectOpNode:
        raw_op_type = op_dict.get("op_type")
        is_all = raw_op_type == OpType.INTERSECT_ALL

        base_args = cls.extract_binary_commons(node_id, op_dict)

        return cls(
            **base_args,
            op_type=OpType.INTERSECT_ALL if is_all else OpType.INTERSECT,
            is_all=is_all,
        )

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
        #raggruppamenti
        OpType.GROUP_BY: GroupByOpNode,
        OpType.WINDOW_GROUP_BY: WindowGroupOpNode,
        #congiunzioni
        OpType.JOIN_WINDOW: WindowJoinOpNode,
        OpType.JOIN_INTERVAL: IntervalJoinOpNode,
        #operazioni insiemistiche, sono famiglie in cui c'è un check is_all
        OpType.UNION: UnionOpNode,
        OpType.UNION_ALL: UnionOpNode,
        OpType.INTERSECT: IntersectOpNode,
        OpType.INTERSECT_ALL: IntersectOpNode,
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
