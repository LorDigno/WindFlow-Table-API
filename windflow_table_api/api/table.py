from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from .draft import Draft
from .expressions import Expression, col
from .operators import *
from .schema import Schema
from .windows import Interval, Window, WindowType
if TYPE_CHECKING:
    from .table_env import TableEnvironment


class Table:
    """
    Rappresenta un Data Stream all'interno della Table API di WindFlow.
    """

    def __init__(
        self,
        schema: Schema,
        table_id: str,
        env: TableEnvironment,
        parent_table: Optional[str] = None,
    ) -> None:
        """Inizializza una Table con lo schema di input, id univoco e riferimento all'ambiente."""

        self._schema = schema
        self._table_id = table_id
        self._env = env
        self._parent_table = parent_table
        
        self._draft: Optional[Draft] = None
        self._draft_name: Optional[str] = None 

    # -------------------------------------------------------------------------
    # Proprietà e Accessori
    # -------------------------------------------------------------------------
    @property
    def schema(self) -> Schema:
        """Restituisce lo Schema corrente della tabella."""
        return self._schema

    @property
    def table_id(self) -> str:
        """Restituisce l'identificativo univoco della tabella assegnato dall'ambiente o custom."""
        return self._table_id

    @property
    def env(self) -> TableEnvironment:
        """Restituisce il riferimento al TableEnvironment di appartenenza."""
        return self._env

    # -------------------------------------------------------------------------
    # Gestione del Draft / DAG Operatori
    # -------------------------------------------------------------------------
    def is_drafting(self) -> bool:
        """Verifica se la tabella ha una catena di operatori in fase di costruzione."""
        return self._draft != None

    def get_draft(self) -> Draft:
        """
        Restituisce il Draft corrente.
        Se non esiste ne crea uno nuovo vuoto.
        """

        if not self._draft:
            self._draft = Draft(self.table_id, self.schema, self._draft_name)

        return self._draft    

    def clear_draft(self) -> None:
        """Azzera lo stato del Draft interno."""
        self._draft = None
        self._draft_name = None

    def name_draft(self, name: str) -> None:
        """
        Assegna il nome al prossimo Draft che sarà il table_id della query risultante.
        Non si può chiamare durante il drafting ma solo prima.
        """

        if self.is_drafting():
            raise RuntimeError(
                f"Impossibile impostare il nome del draft '{name}': "
                f"la composizione del Draft sulla tabella '{self._table_id}' è già iniziata."
            )
        self._draft_name = name

    # -------------------------------------------------------------------------
    # Operatori Unari
    # -------------------------------------------------------------------------
    def where(self, condition: Expression) -> Table:
        """
        Applica un predicato booleano per filtrare i record dello stream.
        Il predicato deve essere un'Expression.
        """

        draft = self.get_draft()
        where_op = WhereOp(condition, draft.current_schema)
        draft.add_unary_operator(where_op)

        return self

    def select(self, *columns: Union[str, Expression], distinct: bool = False) -> Query:
        """
        Proietta o calcola nuove colonne a partire da nomi o espressioni.
        Finalizza la nuova Query nell'ambiente e la rende.
        Con distinct = True aggiunge un operatori di Distinct a seguito della selezione. 
        """

        draft = self.get_draft()

        selections = []
        for c in columns:
            if isinstance(c, str):
                selections.append(col(c))
            elif isinstance(c, Expression):
                selections.append(c)
            else:
                raise TypeError(
                    f"Tipo non supportato all'interno di select(): {type(c).__name__}. "
                    f"Atteso 'str' o 'Expression'."
                )

        if isinstance(draft.get_last_operator(), GroupByOp):
            selections = draft.handle_group(selections)
       
        select_op = SelectOp(selections, draft.current_schema)
        draft.add_unary_operator(select_op)

        if distinct:
            distinct_op = DistinctOp(draft.current_schema)
            draft.add_unary_operator(distinct_op)
             
        q = self.env.create_query(
            draft.current_schema,
            self._table_id,
            draft.get_last_operator(),
            draft.custom_name
        )

        self.clear_draft()

        return q

    def add_columns(self, *expressions: Expression) -> Query:
        """
        Calcola e aggiunge una o più colonne allo schema esistente per creare un nuova Query.
        Richiede di passare l'espressioni con cui calcolare le nuove colonne,
        si consiglia di dargli un nome con .alias("nome").
        Implementato tramite un operatore di select.
        """

        selections: List[Union[str, Expression]] = []
        draft = self.get_draft()

        for c in draft.current_schema.get_columns():
            selections.append(col(c)) 
        for e in expressions:
            if not isinstance(e, Expression):
                raise TypeError(
                    f"Gli argomenti di add_columns devono essere di tipo Expression, "
                    f"ricevuto: {type(e).__name__}. "
                    f"Usa col('nome') o lit(valore) per costruire espressioni."
                )
            selections.append(e)
           
        return self.select(*selections)

    def drop_columns(self, *column_names: str) -> Query:
        """
        Rimuove una o più colonne dallo schema esistente per creare un nuova Query.
        Implementato tramite un operatore di select.
        """

        draft = self.get_draft()

        current_cols = []
        for c in draft.current_schema.get_columns():
            current_cols.append(c)    

        cols_to_drop = []             
        for cn in column_names:
            cols_to_drop.append(cn)

        selections:List[Union[str, Expression]] = [c for c in current_cols if c not in cols_to_drop]

        if not selections:
            raise RuntimeError(
                f"L'operazione drop_columns non è valida: rimuoverebbe tutte le colonne dallo schema."
            )
                   
        return self.select(*selections)

    def rename_columns(self, mapping: Dict[str, str]) -> Query:
        """
        Rinomina una colonna esistente nello schema mantenendone il DataType per creare una nuova Query.
        Accetta un dizionario con struttura {"vecchio_nome": "nuovo_nome"}.
        Implementato tramite un operatore di select.
        """

        if not isinstance(mapping, dict):
            raise TypeError(
                f"L'argomento 'mapping' deve essere un dizionario, "
                f"ricevuto: {type(mapping).__name__}"
            )

        if not mapping:
            raise ValueError("Il dizionario delle rinomine non può essere vuoto.")

        draft = self.get_draft()
        current_schema = draft.current_schema            

        for old_name in mapping:
            if not current_schema.has_field(old_name):
                raise KeyError(
                    f"Impossibile rinominare la colonna '{old_name}': "
                    f"non è presente nello schema corrente {current_schema}"
                ) 

        selections: List[Union[str, Expression]] = []
        for col_name in current_schema.get_columns():
            if col_name in mapping:
                new_name = mapping[col_name]
                selections.append(col(col_name).alias(new_name))
            else:
                selections.append(col(col_name))

        return self.select(*selections)           
        
    def group_by(self, *keys: str, window: Optional[Window] = None) -> Table:
        """
        Definisce le chiavi di raggruppamento per le aggregazioni successive.
        Se si passa una finestra si ha semantica Windowed.
        Stato potenzialmente infinito in base al numero di valori unici per le chiavi.
        """

        if not keys:
            raise ValueError("È necessario specificare almeno una colonna come chiave di raggruppamento in group_by().")

        draft = self.get_draft()
        group_op = GroupByOp(draft.current_schema, list(keys), window)
        draft.add_unary_operator(group_op)

        return self

    def distinct(self) -> Table:
        """
        Rimuove i record duplicati.
        Per fare "SELECT(DISTINCT ...)" usare select_distinct.
        Stato potenzialmente infinito in base al numero di tuple uniche.
        """

        draft = self.get_draft()
        distinct_op = DistinctOp(draft.current_schema)
        draft.add_unary_operator(distinct_op)

        return self

    # -------------------------------------------------------------------------
    # Operatori Binari 
    # -------------------------------------------------------------------------
    def join(
        self,
        other: Table,
        on: str,
        attachment: Optional[Union[Interval, Window]] = None
    ) -> Table:
        """
        Esegue una Join (Inner, Interval, Window) tra questa tabella e un'altra tabella target.
        Se si passa una finestra o un intervallo esegue Window o Interval Join
        Stato potenzialmente infinito in base al numero di tuple uniche in Inner.
        La WindowJoin è possibile solo con finestre temporali.
        """

        if not isinstance(other, Table):
            raise TypeError(
                f"L'operazione di join richiede un'altra istanza di Table, "
                f"ricevuto: {type(other).__name__}"
            )

        if isinstance(attachment, Window) and attachment.window_type == WindowType.COUNT:
            raise TypeError(
                f"L'operazione di window_join è supportata solo su finestre temporali! "
                f"ricevuto: {attachment}"
            )

        draft = self.get_draft()
        join_op = JoinOp(on, draft.current_schema, other.schema, attachment)
        draft.add_binary_operator(join_op, TableRefOp(other.table_id, other.schema))

        return self

    def _apply_set_op(self, other: Table, op_type: SetOpType) -> Table:
        """
        Helper privato per la gestione unificata delle operazioni insiemistiche.
        """

        if not isinstance(other, Table):
            raise TypeError(
                f"L'operazione {op_type.value} richiede un'altra istanza di Table, "
                f"ricevuto: {type(other).__name__}"
            )

        draft = self.get_draft()

        right_ref = TableRefOp(other.table_id, other.schema)
        set_op = SetOp(
            op_type,
            draft.current_schema,
            other.schema
        )
        draft.add_binary_operator(set_op, right_ref)

        return self

    def union_all(self, other: Table) -> Table:
        """Unisce due stream compatibili per schema senza togliere i duplicati."""
        return self._apply_set_op(other, SetOpType.UNION_ALL)

    def union(self, other: Table) -> Table:
        """
        Unisce due stream compatibili togliendo i duplicati.
        Equivalente a union_all seguita da distinct.
        Stato potenzialmente infinito in base al numero di tuple uniche.
        """            
        return self._apply_set_op(other, SetOpType.UNION)

    def intersect(self, other: Table) -> Table:
        """
        Calcola l'intersezione tra le tuple di due stream.
        Stato potenzialmente infinito in base al numero di tuple uniche.
        """
        return self._apply_set_op(other, SetOpType.INTERSECT)

    def intersect_all(self, other: Table) -> Table:
        """
        Calcola l'intersezione tra le tuple di due stream con semantica da multinsieme.
        Stato potenzialmente infinito in base al numero di tuple uniche.
        """
        return self._apply_set_op(other, SetOpType.INTERSECT_ALL)

    # -------------------------------------------------------------------------
    # Rappresentazione
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        """Rappresentazione testuale della Table con id e schema."""
        return (
            f"{self.__class__.__name__}("
            f"id={self._table_id}, "
            f"schema={self.schema},"
            f"env={self.env}"
            f")"
        )

class Query(Table):
    """
    Rappresenta una Table derivata a seguito di una select.
    Contiene il riferimento all'operatore radice del sotto-DAG che l'ha generata.
    """

    def __init__(
        self,
        schema: Schema,
        table_id: str,
        parent_table: str,
        env: TableEnvironment,
        root_operator: Operator
    ) -> None:
        super().__init__(schema=schema, table_id=table_id, env=env, parent_table=parent_table)
        self._root_operator = root_operator

    @property
    def root_operator(self) -> Operator:
        """Restituisce l'operatore radice del sotto-DAG di questa Query."""
        return self._root_operator

    def __repr__(self) -> str:
        return f"Query(id='{self.table_id}', schema={self.schema})"    
