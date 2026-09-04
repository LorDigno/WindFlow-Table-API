from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from .schema import Schema, SchemaBuilder, Field
from .expressions import Expression, ColRefExpression, AggregateExpression
from .durations import TimeCol
from .windows import Window, Interval, WindowType
from .datatypes import DataTypes
from .file_config import InputFileConfiguration

class Operator(ABC):
    """
    Classe base astratta per tutti i nodi logici degli operatori di WindFlow.
    Rappresenta un'operazione sullo stream che riceve uno o più schemi in input
    e produce uno schema in output.
    Lo schema di output viene generalmente calcolato dinamicamente in base alla query.
    """

    def __init__(
        self, 
        schema_out: Schema, 
        input_schema: Schema, 
        parents: Optional[List[Operator]] = None
    ) -> None:
        self._schema_out = schema_out
        self._input_schema = input_schema
        self._parents: List[Operator] = parents if parents is not None else []

    @property
    def schema_out(self) -> Schema:
        """Restituisce lo schema calcolato prodotto in uscita dall'operatore."""
        return self._schema_out

    @property
    def input_schema(self) -> Schema:
        """Restituisce lo schema in ingresso dell'operatore."""
        return self._input_schema

    @property
    def parents(self) -> List[Operator]:
        """Restituisce la lista degli operatori connessi in input."""
        return self._parents

    @abstractmethod
    def set_parents(self, parents: List[Operator]) -> None:
        """Imposta/sovrascrive la lista degli operatori parent."""
        pass

    @abstractmethod
    def get_op_type(self) -> str:
        """Restituisce l'identificativo univoco del tipo di operatore."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializza l'operatore e la sua configurazione in un dizionario
        utilizzato per la generazione del JSON.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type='{self.get_op_type()}', out_schema={self._schema_out})"

# -------------------------------------------------------------------------
# Operatori senza parent
# -------------------------------------------------------------------------

class FromOp(Operator): 
    """
    Operatore foglia senza parents. 
    Rappresenta l'origine dei dati (sorgente o tabella madre).
    """

    def __init__(
        self, source_table_id: str, 
        file_config: InputFileConfiguration
    ) -> None:
        super().__init__(schema_out=file_config.schema, input_schema=SchemaBuilder().build(), parents=[])
        self.source_table_id = source_table_id    
        self.config = file_config

    def get_op_type(self) -> str:
        return "FROM"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "source_id": self.source_table_id,
            "schema_out": self.schema_out.to_dict(),
            "config": self.config.to_dict()
        }

    def set_parents(self, parents: List[Operator]) -> None:
            """Nega la possibilità di aggiunta."""
            
            raise RuntimeError("Non si possono aggiungere parents al From")

class TableRefOp(Operator): 
    """
    Operatore foglia senza parents. 
    Rappresenta un'altra tabella a da cui arrivano dati.
    """

    def __init__(
        self, 
        source_table_id: str, 
        schema_out: Schema, 
    ) -> None:
        super().__init__(schema_out=schema_out, input_schema=SchemaBuilder().build(), parents=[])
        self.source_table_id = source_table_id     

    def get_op_type(self) -> str:
        return "TAB_REF"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "source_id": self.source_table_id,
            "schema_out": self.schema_out.to_dict()
        }

    def set_parents(self, parents: List[Operator]) -> None:
            """Nega la possibilità di aggiunta."""
            
            raise RuntimeError("Non si possono aggiungere parents al TableRef")

# -------------------------------------------------------------------------
# Sottoclassi Specializzate per Arietà
# -------------------------------------------------------------------------

class UnaryOperator(Operator, ABC):
    """
    Classe base per operatori a singolo ingresso come Filter, Select, GroupBy.
    """

    def __init__(self,
                schema_out: Schema, 
                input_schema: Schema, 
                parent: Optional[Operator] = None
        ) -> None:
        parents = [parent] if parent is not None else []
        super().__init__(schema_out=schema_out, input_schema=input_schema, parents=parents)

    @property
    def parent(self) -> Optional[Operator]:
        """Restituisce l'unico operatore parent se presente."""
        return self._parents[0] if self._parents else None

    def set_parents(self, parents: List[Operator]) -> None:
        """
        Imposta/sovrascrive la lista degli operatori parent.
        Se passata una lista di più di un operatore solleva un errore.
        """

        if len(parents) != 1:
            raise RuntimeError("Non si possono aggiungere più parents ad un operatore unario")
        else:
            self._parents = parents

class BinaryOperator(Operator, ABC):
    """
    Classe base per operatori a doppio ingresso come Join, Union e Intersect.
    """

    def __init__(
        self,
        schema_out: Schema,
        input_schema: Schema,
        left_parent: Optional[Operator] = None,
        right_parent: Optional[Operator] = None,
    ) -> None:
        parents = []
        if left_parent:
            parents.append(left_parent)
        if right_parent:
            parents.append(right_parent)
        super().__init__(schema_out=schema_out, input_schema=input_schema, parents=parents)

    @property
    def left_parent(self) -> Optional[Operator]:
        return self._parents[0] if len(self._parents) > 0 else None

    @property
    def right_parent(self) -> Optional[Operator]:
        return self._parents[1] if len(self._parents) > 1 else None
    
    def set_parents(self, parents: List[Operator]) -> None:
        """
        Imposta/sovrascrive la lista degli operatori parent.
        Se passata una lista senza esattamente due operatori solleva un errore.
        Il primo diventa il left_parent e il secondo il right_parent,
        """
    
        if len(parents) != 2:
            raise RuntimeError("Devono esserci esattamente 2 parents in un operatore binario")
        else:
            self._parents = parents

# -------------------------------------------------------------------------
# Sottoclassi Specializzate per ogni Operazione
# -------------------------------------------------------------------------    

class SelectOp(UnaryOperator):
    """
    Rappresenta l'operatore di proiezione e i vari operatori di modifica allo schema.
    Costruisce un nuovo Schema di output inferendo nomi e tipi di dato da ciascuna Expression fornita.
    """

    def __init__(
        self,
        expressions: List[Expression],
        input_schema: Schema,
    ) -> None:
        
        if not expressions:
            raise RuntimeError("La clausola select richiede almeno un'espressione di proiezione.")

        builder = SchemaBuilder()
        for expr in expressions:
            #add_expression calcola col_name, col_type e mantiene l'espressione
            builder.add_expression(expr, input_schema)

        super().__init__(schema_out=builder.build(), input_schema=input_schema)
        self.expressions = expressions

    def get_op_type(self) -> str:
        return "SELECT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "expressions": [expr.to_dict(self.input_schema) for expr in self.expressions],
            "schema_in": self.input_schema.to_dict(),
            "schema_out": self.schema_out.to_dict()
        }

class WhereOp(UnaryOperator):
    """
    Rappresenta un operatore di filtraggio basato su una condizione booleana.
    Filtra gli elementi in ingresso senza alterare lo schema dello stream.
    """

    def __init__(
        self,
        condition: Expression,
        input_schema: Schema,
    ) -> None:

        cond_type = condition.get_type(input_schema)
        if cond_type != DataTypes.BOOLEAN:
            raise TypeError(
                f"La condizione di filtraggio deve restituire un valore BOOLEAN, "
                f"ma l'espressione fornita restituisce il tipo: {cond_type.name}"
            )

        super().__init__(schema_out=input_schema, input_schema=input_schema)
        self.condition = condition

    def get_op_type(self) -> str:
        return "WHERE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "condition": self.condition.to_dict(self.input_schema),
            "schema_out": self.schema_out.to_dict(),
            "schema_in": self.input_schema.to_dict()
        }

class GroupByOp(UnaryOperator):
    """
    Classe che rappresenta l'operatore di GroupBy.
    L'operatore TableAPI mantiene lo stesso schema ricevuto in input ma nel JSON per 
    l'istanziazione WF avrà uno schema di output definito in base alle aggregazioni della select.
    """

    def __init__(
        self,
        input_schema: Schema,
        keys: List[str],
        window: Optional[Window] = None
    ) -> None: 

        #controllo che lo schema abbia la chiave
        for key in keys:
            if not input_schema.has_field(key):
                raise RuntimeError(
                    f"La colonna di raggruppamento '{key}' non è presente nello schema: {input_schema}"
                )

        #si mantiene lo stesso schema dato che le aggregazioni sono in select
        super().__init__(schema_out=input_schema, input_schema=input_schema)

        self.keys = keys
        self.window = window
        self.aggregations: List[AggregateExpression] = []

    def get_op_type(self) -> str:
        if self.window is None:
            return "GROUP_BY"
        return "WINDOW_GROUP_BY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "keys": self.keys,
            "window": self.window.to_dict() if self.window else None,
            "schema_out": self.schema_out.to_dict(),   
            "schema_in": self.input_schema.to_dict(),
            "aggregations": [ag.to_dict(self.input_schema) for ag in self.aggregations]
        }

class DistinctOp(UnaryOperator):
    """
    Rappresenta l'operatore di distinzione sullo stream corrente.
    """

    def __init__(
            self, 
            input_schema: Schema
        ) -> None:
            super().__init__(schema_out=input_schema, input_schema=input_schema)

    def get_op_type(self) -> str:
        return "DISTINCT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "schema_out": self.schema_out.to_dict(),
            "schema_in": self.input_schema.to_dict()
        }

class JoinOp(BinaryOperator):
    """
    Classe che rappresenta gli operatori di Inner/INterval/Windowed Join in base ai parametri dati.
    """

    def __init__(
        self,
        keys: List[str],
        tab1_schema: Schema,
        tab2_schema: Schema,
        attachment: Optional[Union[Window, Interval]]
    ) -> None:
        if len(keys) < 1:
            raise  ValueError(
                f"L'operazione di join è supportata solo su con almeno una chiave."
            )
                
        if isinstance(attachment, Window) and attachment.window_type == WindowType.COUNT:
            raise TypeError(
                f"L'operazione di window_join è supportata solo su finestre temporali! "
                f"ricevuto: {attachment}"
            )
        
        #interrompo se non hanno la chiave in comune con lo stesso tipo
        for key in keys:
            if not tab1_schema.has_field(key):
                raise RuntimeError(f"La tabella di sinistra non ha la key: {key}")
            if not tab2_schema.has_field(key):
                raise RuntimeError(f"La tabella di destra non ha la key: {key}")
            if not (tab1_schema.get_type_for(key) == tab2_schema.get_type_for(key)):
                raise RuntimeError(f"Le due tabelle hanno tipi diversi per la key: {key}")

            #calcolo lo schema di output
            builder = SchemaBuilder().add_column(key, tab1_schema.get_type_for(key))

        #aggiungo gli attributi di tab1
        for f in tab1_schema.get_columns():
            current = tab1_schema.get_field(f)
            if current.name in keys:
                continue
            builder.add_column(current.name, current.data_type) 

        #aggiungo gli attributi di tab2
        for f in tab2_schema.get_columns():
            current = tab2_schema.get_field(f)
            if current.name in keys:
                continue
            builder.add_column(current.name, current.data_type)         

        super().__init__(schema_out=builder.build(), input_schema=tab1_schema)

        self.keys = keys
        self.tab1_schema = tab1_schema
        self.tab2_schema = tab2_schema
        self.attachment = attachment

    def get_op_type(self) -> str:
        if self.attachment is None:
            return "JOIN_INNER"
        return f"JOIN_{self.attachment.__class__.__name__.upper()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "keys": self.keys,
            "attachment": self.attachment.to_dict() if self.attachment else None,
            "tab1_schema": self.tab1_schema.to_dict(),
            "tab2_schema": self.tab2_schema.to_dict(),
            "schema_out": self.schema_out.to_dict()
        }

class SetOpType(Enum):
    UNION = "UNION"
    UNION_ALL = "UNION_ALL"
    INTERSECT = "INTERSECT"
    INTERSECT_ALL = "INTERSECT_ALL"

class SetOp(BinaryOperator):
    """
    Classe che rappresenta gli operatori insiemistici Union/UnionAll/Intersect/IntersectAll.
    """

    def __init__(
        self,
        set_op_type:SetOpType,
        tab1_schema: Schema,
        tab2_schema: Schema,
    ) -> None:
        
        #controllo che gli schemi siano identici a scapito dell'ordine
        if not(tab1_schema == tab2_schema):
            raise RuntimeError(f"{set_op_type.value} si può fare solo su tabelle a schema uguale")

        super().__init__(schema_out=tab1_schema, input_schema=tab1_schema)
        self.set_op_type = set_op_type
        #salvo lo schema di tab2 per un'eventuale conversione nel C++
        self.tab2_schema = tab2_schema

    def get_op_type(self) -> str:
        return self.set_op_type.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.get_op_type(),
            "schema_out": self.schema_out.to_dict(),
            "tab1_schema": self.input_schema.to_dict(),
            "tab2_schema": self.tab2_schema.to_dict()
        }
    