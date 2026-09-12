from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Type, Tuple
from abc import abstractmethod, ABC
from windflow_table_api import OpType, WindowKind, WindowType, TimeUnits, FileFormat, TimeFormats
from .schema_gen import SchemaGenerator, CppStruct, CppField
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator
from .builder_generator import BuilderGenerator
from .utility import get_aggregate_default

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
    build_gen: BuilderGenerator

    #variabili passate dall'explorer
    operations_counter: int      
    par: int 

@dataclass
class VisitResult:
    """Informazioni restituite dalla visita di un nodo."""
    out_struct: CppStruct

    #stringhe da accumulare nelle pipe corrispondenti
    pipe_additions: Dict[str, str] = field(default_factory=dict)

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
    schema_out: Dict[str, str]

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

    def get_map_builder(
        self,
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        var_name: str,
        ctx: VisitContext
    ) -> str:
        """
        Rende la stringa di un SelectBuilder per implementare una map, genera la lambda automaticamente.
        Utilizzato dal SelectOpNode e altri nodi che richiedono tagging (intersect, join).
        """

        map_func = ctx.lambda_gen.map_lambda(
            in_struct=in_struct,
            out_struct=out_struct,
            mappings=mappings,
            input_var="in",
        )

        builder = ctx.build_gen.select_builder(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            map_func=map_func,
            op_name=var_name,
            par=ctx.par
        )
        return builder

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OpNode):
            return self.node_id == other.node_id
        return False

#classi per non duplicare i parsing degli attributi comuni in base all'arietà e utilizzo di finestre

@dataclass(kw_only=True)
class UnaryNode(OpNode, ABC):
    schema_in: Dict[str, str]

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
    left_schema: Dict[str, str]
    right_schema: Dict[str, str]

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
    window_type: str
    window_kind: str
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
    time_col:Optional[str] = None       #nome
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

    def visit(self, ctx: VisitContext) -> VisitResult:
        #genero lo struct di output
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict= self.schema_out,
            name_hint= "source_" + self.node_id
        )

        #funzione che esecue il parsing da dare al builder
        parser_func = ctx.lambda_gen.parser_lambda(
            struct_out= struct_out.struct_name,
            time_col_name= self.time_col,
            time_format= self.time_format,
            ordered_fields= [
                {"name": col_name, "type": col_type}
                for col_name, col_type in self.schema_out.items()
            ]
        )

        #nome di variabile
        ctx.operations_counter += 1
        var_name = f"from_{ctx.operations_counter}_op"

        #genero il builder
        builder_str =ctx.build_gen.source_builder(
            var_name=var_name,
            out_struct=struct_out.struct_name,
            filepath=self.filepath,
            parser_func= parser_func,
            op_name=self.node_id,
            has_header=self.header,
            event_time=self.time_col is not None,
            is_ordered=self.ordered,
            delay=self.delay,
            par= ctx.par,
            split_size= self.split_size
        )

        #aggiunta alla pipe
        pipe_str = f"auto& {ctx.pipe} = topology.add_source({var_name})"

        return VisitResult(
            out_struct= struct_out,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str]
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

    def visit(self, ctx: VisitContext) -> VisitResult:
        #struct di input
        parent_struct = ctx.parent_structs[0]

        #traduco la condizione e genero la lambda
        translated_cond = ctx.expr_tl.translate_expr(self.condition)
        filt_func = ctx.lambda_gen.where_lambda(
            in_struct= parent_struct.struct_name,
            condition= translated_cond
        )

        #nome di variabile
        node_count = ctx.operations_counter + 1
        var_name = f"where_{node_count}_op"

        #generazione del builder
        builder_str = ctx.build_gen.where_builder(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            filt_func= filt_func,
            op_name= self.node_id,
            par= ctx.par
        )

        #aggiunta alla pipe
        pipe_str = f".add({var_name})"

        return VisitResult(
            out_struct= parent_struct,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str],
        )

@dataclass(kw_only=True)
class SelectOpNode(UnaryNode):
    """Nodo unario di proiezione scalare e mappatura colonne."""

    op_type:OpType = OpType.SELECT
    expressions: List[Dict[str, Any]]

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

    def visit(self, ctx: VisitContext) -> VisitResult:
        #struct di input
        parent_struct = ctx.parent_structs[0]

        #generazione struct di output
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict= self.schema_out,
            name_hint= self.node_id + "_struct_out",
        )

        #inferisco i mappings di selezione
        mappings: List[Tuple[str, str]] = []
        for e in self.expressions:
            #traduco l'espressione da assegnare
            value = ctx.expr_tl.translate_expr(e)

            #ricavo il nome
            target = e.get("alias") if e.get("alias") else e.get("name")
            if not target:
                raise KeyError(
                    f"Chiave 'alias' e 'name' assenti nell'espressione di selezione {e}"
                )

            mappings.append((target, value))

        #nome di variabile
        node_count = ctx.operations_counter + 1
        var_name = f"select_{node_count}_op"

        #generazione del builder
        builder_str = self.get_map_builder(
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            mappings= mappings,
            var_name= var_name,
            ctx= ctx
        )

        #aggiunta alla pipe
        #possibile chain mode?
        pipe_str = f".add({var_name})"

        return VisitResult(
            out_struct= struct_out,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str]
        )

@dataclass(kw_only=True)
class DistinctOpNode(UnaryNode):
    """
    Nodo unario di deduplicazione in-stream dello schema di input.
    Si programma una futura implementazione con state-cleaning.
    """

    op_type:OpType = OpType.DISTINCT

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> DistinctOpNode:
        base_args = cls.extract_unary_commons(node_id, op_dict)
        return cls(
            **base_args
        )

    def visit(self, ctx: VisitContext) -> VisitResult:
        #richiede la hash sull'input per le hash_map
        parent_struct = ctx.parent_structs[0]
        parent_struct.needs_hash = True

        #generazione della lambda di estrazione della chiave
        key_lambda = None
        if ctx.par > 1:
            #in questo caso si tratta di rendere l'intero struct ricevuto in input

            key_lambda = (
                f"[](const {parent_struct.struct_name}& in) -> {parent_struct.struct_name} {{ return in; }}"
            )

        #nome di variabile
        node_count = ctx.operations_counter + 1
        var_name = f"distinct_{node_count}_op"

        #generazione builder (il distinct non richiede una lambda)
        builder_str = ctx.build_gen.distinct_builder(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            key_struct= parent_struct.struct_name,
            key_lambda= key_lambda, 
            op_name= self.node_id,
            par = ctx.par
        )
        
        #aggiunta alla pipe
        pipe_str = f".add({var_name})"

        return VisitResult(
            out_struct= parent_struct,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str]
        )

#---- Raggruppamenti

@dataclass(kw_only=True)
class GroupByNode(UnaryNode, ABC):
    """
    Classe base astratta per tutti gli operatori di raggruppamento unario.
    """

    keys: List[str] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def extract_group_commons(cls, node_id:str, op_dict:Dict[str, Any]) -> Dict[str, Any]:
        keys = op_dict.get("keys")
        if keys is None:
            raise KeyError(
                f"Chiave 'keys' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        aggregations = op_dict.get("aggregations")
        if aggregations is None:
            raise KeyError(
                f"Chiave 'aggregations' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        base_args = cls.extract_unary_commons(node_id, op_dict) 

        return {
            **base_args,
            "keys": keys,
            "aggregations": aggregations,
        }

    def get_aggregations_exprs(
        self, 
        expr_tl: ExpressionTranslator
        ) -> Tuple[List[str], Dict[str, str]]:
        """
        Metodo che rende la lista delle aggregazioni tradotte in accumulatori e il dizionario dei default.
        (in questo ordine come tupla)
        """

        accs = []
        defaults = {}
        for a in self.aggregations:
            #accumulatore
            accs.append(expr_tl.translate_aggregate(a)) 

            #valore di dafault dell'accumulatore
            defaults[a["name"]] = get_aggregate_default(a["func"], a["data_type"])

        return (accs, defaults)

    def get_keyBy(
        self,
        parent_struct:CppStruct, 
        sch_gen: SchemaGenerator,
        lambda_gen: LambdaGenerator
        ) -> Tuple[CppStruct, str]:
        """
        Metodo che gestisce la necessità di un keyBy in base alla presenza di chiavi di raggruppamento.
        Rende (keyByStruct, keyByLambda_str).
        Se non ci sono chiavi di raggruppamento solleva un ValueError.
        """

        key_schema:Dict[str, str] = {}
        if len(self.keys) > 0:
            #se sono presenti chiavi di raggruppamento uso solo quelle per il groupBy 
            for k in self.keys:
                key_schema[k] = self.schema_in[k]
        else:
            raise ValueError(
                f"Non si può fare il keyBy senza avere chiavi di raggruppamento in un GroupBy"
            )              

        #genero lo struct del keyBy
        key_struct = sch_gen.get_or_create_struct(
            schema_dict= key_schema,
            name_hint= self.node_id + "_key_struct",
            needs_hash=True
        )  

        mappings = []
        for k in key_schema:
            mappings.append((k, f"in.{k}"))

        #genero la lambda di estrazione del keyBy
        key_lambda = lambda_gen.map_lambda(
            in_struct= parent_struct.struct_name,
            out_struct= key_struct.struct_name,
            mappings= mappings,
            input_var= "in"
        )

        return key_struct, key_lambda

    def _prepare_group_context(self, ctx: VisitContext, is_windowed: bool):
        """Prepara le dipendenze C++ condivise (accumulatori, keyBy, struct_out, lambda)."""
        #schema di input
        parent_struct = ctx.parent_structs[0]

        #accumulatori
        accs = []
        defaults = {}
        accs, defaults = self.get_aggregations_exprs(ctx.expr_tl)

        #gestione del keyBy
        needs_keyBy = len(self.keys) > 0 and (ctx.par > 1)
        keyBy_struct = None
        keyBy_lambda = None
        if needs_keyBy:
            keyBy_struct, keyBy_lambda = self.get_keyBy(parent_struct, ctx.sch_gen, ctx.lambda_gen)

        #generazione struct di output
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict=self.schema_out,
            name_hint=f"{self.node_id}_struct_out",
            needs_win=is_windowed,
            win_key_struct=keyBy_struct,
            defaults=defaults,
        )

        #lambda di aggregazione
        lambda_func = ctx.lambda_gen.groupBy_lambda(
            in_struct=parent_struct.struct_name,
            out_struct=struct_out.struct_name,
            keys=self.keys,
            accumulations=accs,
            in_var="in",
            out_var="out",
        )

        return parent_struct, struct_out, lambda_func, keyBy_struct, keyBy_lambda, needs_keyBy

@dataclass(kw_only=True)
class GlobalGroupOpNode(GroupByNode):
    """
    Nodo stateful di raggruppamento e aggregazione globale.
    """

    op_type:OpType = OpType.GLOBAL_GROUP_BY 

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> GlobalGroupOpNode:
        base_args = cls.extract_group_commons(node_id, op_dict)
        return cls(
            **base_args
        ) 

    def visit(self, ctx: VisitContext) -> VisitResult:
        #chiamata alla visita condivisa dei tipi di groupBy
        (
            parent_struct,
            struct_out,
            lambda_func,
            keyBy_struct,
            keyBy_lambda,
            needs_keyBy,
        ) = self._prepare_group_context(ctx, is_windowed=False)

        #nome di variabile
        node_count = ctx.operations_counter + 1
        var_name = f"global_group_{node_count}_op"

        #generazione del builder
        builder_str = ctx.build_gen.group_builder(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            lambda_func= lambda_func,

            op_name= self.node_id,
            par= ctx.par if needs_keyBy else 1,

            needs_key= needs_keyBy,
            key_struct= keyBy_struct.struct_name if keyBy_struct else None,
            key_lambda= keyBy_lambda,

            is_windowed= False
        )

        #aggiunta alla pipe
        pipe_str = f".add({var_name})"

        return VisitResult(
            out_struct= struct_out,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str]
        )

@dataclass(kw_only=True)
class WindowGroupOpNode(GroupByNode, WindowNode):
    """
    Nodo stateful di raggruppamento e aggregazione con finestra.
    """

    op_type:OpType = OpType.WINDOW_GROUP_BY

    @classmethod
    def from_dict(cls, node_id: str, op_dict: Dict[str, Any]) -> WindowGroupOpNode:
        #parsing dei vari attributi della finestra
        window:Dict[str, Any] = op_dict.get("window", {})
        win_args:Dict[str, Any] = cls.extract_window(window, op_dict)           

        base_args:Dict[str, Any] = cls.extract_group_commons(node_id, op_dict)

        return cls(
            **base_args,
            **win_args,
        ) 

    def visit(self, ctx: VisitContext) -> VisitResult:
        #chiamata alla visita condivisa dei tipi di groupBy
        (
            parent_struct,
            struct_out,
            lambda_func,
            keyBy_struct,
            keyBy_lambda,
            needs_keyBy,
        ) = self._prepare_group_context(ctx, is_windowed=True)

        #nome di variabile
        node_count = ctx.operations_counter + 1
        var_name = f"window_group_{node_count}_op"

        #generazione del builder
        builder_str = ctx.build_gen.group_builder(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            lambda_func= lambda_func,

            op_name= self.node_id,
            par= ctx.par if needs_keyBy else 1,

            needs_key= needs_keyBy,
            key_struct= keyBy_struct.struct_name if keyBy_struct else None,
            key_lambda= keyBy_lambda,

            is_windowed=True,
            win_type= self.window_type,
            win_size= self.window_size,
            win_slide= self.window_slide
        )

        #aggiunta alla pipe
        pipe_str = f".add({var_name})"

        return VisitResult(
            out_struct= struct_out,
            pipe_additions= {ctx.pipe: pipe_str},
            emitted_builders= [builder_str]
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
        if keys is not None:
            raise KeyError(
                f"Chiave 'keys' mancante nel nodo:\n{op_dict}\nPer la creazione di {cls.op_type}."
            )

        base_args = cls.extract_binary_commons(node_id, op_dict)

        return {
            **base_args,
            "keys": keys
        }

    def get_unifier_map(
        self, 
        ctx:VisitContext, 
        input_struct:CppStruct,
        unified_struct:CppStruct,
        var_name:str
        ) -> str:
        """Rende il builder del map di unificazione dello schema."""

        mappings = []
        for f in input_struct.fields:
            mappings.append((f.name, f"in.{f.name}"))

        return self.get_map_builder(
            in_struct= input_struct.struct_name,
            out_struct= unified_struct.struct_name,
            mappings= mappings,
            var_name= var_name,
            ctx= ctx
        )

    def _prepare_join_context(self, ctx:VisitContext):
        """
        Prepara le dipendenze C++ condivise (unificazione schemi, keyBy, struct_out, lambda).
        Vengono automaticamente messe le map di unificazione in res.pipe_additions e res.builders, ctx.node_counter per questo aumenta di 2.
        """

        #struct di input
        if len(ctx.parent_structs) != 2:
            raise RuntimeError(
                f"Un operatore di join ha ricevuto {len(ctx.parent_structs)} struct di input."
            )
        left_parent_struct = ctx.parent_structs[0]
        right_parent_struct = ctx.parent_structs[1]

        #pipe di input
        if len(ctx.to_merge_pipes) != 2:
            raise RuntimeError(
                f"Un operatore di join ha ricevuto {len(ctx.to_merge_pipes)} pipe in input."
            )
        left_parent_pipe = ctx.to_merge_pipes[0]
        right_parent_pipe = ctx.to_merge_pipes[1]

        #schema unificato
        joined_struct = ctx.sch_gen.struct_join(left_parent_struct, right_parent_struct)

        #struct di output
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict= self.schema_out,
            name_hint= self.node_id + "_struct_out"
        )

        #creazione del risultato di visita
        result = VisitResult(
            out_struct = struct_out
        )

        #inserzione nodi di unificazione schema
        #left
        ctx.operations_counter += 1
        left_map_var = f"left_unifier_{ctx.operations_counter}_op"
        left_map_builder = self.get_unifier_map(
            ctx= ctx,
            input_struct= left_parent_struct,
            unified_struct= joined_struct,
            var_name= left_map_var
        )
        result.emitted_builders.append(left_map_builder)
        result.pipe_additions[left_parent_pipe] = f".add({left_map_var})"

        #right
        ctx.operations_counter += 1
        right_map_var = f"right_unifier_{ctx.operations_counter}_op"
        right_map_builder = self.get_unifier_map(
            ctx= ctx,
            input_struct= right_parent_struct,
            unified_struct= joined_struct,
            var_name= right_map_var
        )
        result.emitted_builders.append(right_map_builder)
        result.pipe_additions[right_parent_pipe] = f".add({right_map_var})"

        #keyBy
        needs_keyBy = ctx.par > 1 and len(self.keys) > 0
        key_lambda = None
        key_struct = None
        if needs_keyBy:
            key_mappings = []
            key_schema = {}
            for k in self.keys:
                key_schema[k] = self.schema_out[k]
                key_mappings.append((k, f"in.{k}"))

            key_struct = ctx.sch_gen.get_or_create_struct(
                schema_dict= key_schema,
                name_hint= self.node_id + "_key_struct",
                needs_hash= True
            )

            key_lambda = ctx.lambda_gen.map_lambda(
                in_struct= joined_struct.struct_name,
                out_struct= key_struct.struct_name,
                mappings= key_mappings,
                input_var= "in"
            )

        #join mappings
        join_mappings = []
        for f in struct_out.fields:
            if f.name in [f.name for f in left_parent_struct.fields]:
                join_mappings.append((f.name, f"left.{f.name}"))
            else:
                join_mappings.append((f.name, f"right.{f.name}")) 

        #join lambda
        join_lambda = ctx.lambda_gen.join_lambda(
            input_struct= joined_struct.struct_name,
            out_struct= struct_out.struct_name,
            mappings= join_mappings,
            left_var= "left",
            right_var= "right",
        )

        return result, joined_struct, join_lambda, needs_keyBy, key_lambda, key_struct

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

    def visit(self, ctx: VisitContext) -> VisitResult:
        (
            result,
            joined_struct,
            join_lambda,
            needs_keyBy,
            key_lambda,
            key_struct
        ) = self._prepare_join_context(ctx)

        ctx.operations_counter += 1
        var_name = f"join_{ctx.operations_counter}_op"

        #generazione builder
        builder_str = ctx.build_gen.join_builder(
            var_name= var_name,
            in_struct= joined_struct.struct_name,
            out_struct= result.out_struct.struct_name,
            join_func= join_lambda,

            needs_key= needs_keyBy,
            key_lambda= key_lambda,
            key_struct= key_struct.struct_name if key_struct else None,

            is_windowed= True,
            win_size= self.window_size,
            win_slide= self.window_slide,

            op_name= self.node_id,
            par= ctx.par
        )
        result.emitted_builders.append(builder_str)

        #aggiunta alla pipe
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe= ctx.pipe,
            branches= ctx.to_merge_pipes,
            branches_var= f"{ctx.pipe}_branches"
        )
        result.pipe_additions[ctx.pipe] = pipe_str + f".add({var_name})"

        return result

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

    def visit(self, ctx: VisitContext) -> VisitResult:
        (
            result,
            joined_struct,
            join_lambda,
            needs_keyBy,
            key_lambda,
            key_struct
        ) = self._prepare_join_context(ctx)

        ctx.operations_counter += 1
        var_name = f"join_{ctx.operations_counter}_op"

        #generazione builder
        builder_str = ctx.build_gen.join_builder(
            var_name= var_name,
            in_struct= joined_struct.struct_name,
            out_struct= result.out_struct.struct_name,
            join_func= join_lambda,

            needs_key= needs_keyBy,
            key_lambda= key_lambda,
            key_struct= key_struct.struct_name if key_struct else None,

            is_windowed= False,
            lower= self.lower,
            upper= self.upper,

            op_name= self.node_id,
            par= ctx.par
        )
        result.emitted_builders.append(builder_str)

        #aggiunta alla pipe
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe= ctx.pipe,
            branches= ctx.to_merge_pipes,
            branches_var= f"{ctx.pipe}_branches"
        )
        result.pipe_additions[ctx.pipe] = pipe_str + f".add({var_name})"

        return result

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

    def visit(self, ctx: VisitContext) -> VisitResult:
        #struct di input
        if len(ctx.parent_structs) != 2:
            raise RuntimeError(
                f"Un operatore di union ha ricevuto {len(ctx.parent_structs)} struct di input."
            )
        left_parent_struct = ctx.parent_structs[0]
        right_parent_struct = ctx.parent_structs[1]
        if right_parent_struct != left_parent_struct:
            raise RuntimeError(
                f"Un operatore di {self.op_type} ha ricevuto due struct diversi in input, {left_parent_struct.struct_name} e {right_parent_struct.struct_name}"
            )

        #unione topologica delle pipes
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe= ctx.pipe,
            branches_var= f"{ctx.pipe}_branches",
            branches= ctx.to_merge_pipes,
            topology_name= "topology"
        )

        #gestione della distinct della Union insiemistica
        builders = []
        if not self.is_all:
            distinct_node = DistinctOpNode(
                node_id= self.node_id + "_distinct",
                schema_out= self.schema_out,
                schema_in= self.left_schema,
            )
            dist_res = distinct_node.visit(ctx)
            builders = dist_res.emitted_builders
            pipe_str += dist_res.pipe_additions[ctx.pipe]
            
        return VisitResult(
            out_struct= left_parent_struct,
            emitted_builders= builders,
            pipe_additions= {ctx.pipe: pipe_str}
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

    def visit(self, ctx: VisitContext) -> VisitResult:
        #struct di input
        if len(ctx.parent_structs) != 2:
            raise RuntimeError(
                f"Un operatore di intersect ha ricevuto {len(ctx.parent_structs)} struct di input."
            )
        left_parent_struct = ctx.parent_structs[0]
        right_parent_struct = ctx.parent_structs[1]
        if right_parent_struct != left_parent_struct:
            raise RuntimeError(
                f"Un operatore di {self.op_type} ha ricevuto due struct diversi in input, {left_parent_struct.struct_name} e {right_parent_struct.struct_name}"
            )

        #hash necessario per le hashmap
        left_parent_struct.needs_hash = True

        #struct di tagging necessario come input
        tagged_struct = f"Tagged_Tuple<{left_parent_struct.struct_name}>"

        #inizializzo il risultato
        result = VisitResult(
            out_struct= left_parent_struct
        )

        #pipe di input
        if len(ctx.to_merge_pipes) != 2:
            raise RuntimeError(
                f"Un operatore di intersect ha ricevuto {len(ctx.to_merge_pipes)} pipe in input."
            )
        left_parent_pipe = ctx.to_merge_pipes[0]
        right_parent_pipe = ctx.to_merge_pipes[1]

        #tagging del left stream
        ctx.operations_counter += 1
        left_var = f"left_tagger_{ctx.operations_counter}_op"
        left_mappings = [
            ("data", "in"),
            ("tag", "0"),
        ]
        left_tagger = self.get_map_builder(
            in_struct= left_parent_struct.struct_name,
            out_struct= tagged_struct,
            mappings= left_mappings,
            var_name= left_var,
            ctx= ctx
        )
        result.pipe_additions[left_parent_pipe] = f".chain({left_var})"
        result.emitted_builders.append(left_tagger)

        #tagging del right stream
        ctx.operations_counter += 1
        right_var = f"right_tagger_{ctx.operations_counter}_op"
        right_mappings = [
            ("data", "in"),
            ("tag", "1"),
        ]
        right_tagger = self.get_map_builder(
            in_struct= right_parent_struct.struct_name,
            out_struct= tagged_struct,
            mappings= right_mappings,
            var_name= right_var,
            ctx= ctx
        )
        result.pipe_additions[right_parent_pipe] = f".chain({right_var})"
        result.emitted_builders.append(right_tagger)

        #nome di variabile
        ctx.operations_counter += 1
        var_name = f"intersect_{ctx.operations_counter}_op"

        #generazione del builder
        builder_str = ctx.build_gen.intersect_builder(
            var_name= var_name,
            in_struct = left_parent_struct.struct_name,
            is_all= self.is_all,
            op_name= self.node_id,
            par = ctx.par
        )
        result.emitted_builders.append(builder_str)

        #aggiunta alla pipe
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe= ctx.pipe,
            branches= ctx.to_merge_pipes,
            branches_var= f"{ctx.pipe}_branches"
        )
        pipe_str += f".add({var_name})"
        result.pipe_additions[ctx.pipe] = pipe_str

        return result
        

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
        OpType.GLOBAL_GROUP_BY: GlobalGroupOpNode,
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
