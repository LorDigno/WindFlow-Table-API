from typing import TYPE_CHECKING, List, Optional, Any, Dict
from .operators import (
    BinaryOperator,
    GroupByOp,
    Operator,
    SelectOp,
    TableRefOp,
    UnaryOperator,
)
from .schema import Schema, SchemaBuilder
from .expressions import Expression, AggregateExpression

class Draft:
    """
    Rappresenta lo stato temporaneo di composizione di una query su una Table.
    Accumula gli operatori intermedi prima della finalizzazione tramite select().
    """

    def __init__(
            self, 
            source_table_id: str,
            source_table_schema: Schema,
            custom_name: Optional[str] = None):
        """
        Crea il Draft vuoto con nome se specificato tramite un precedente table.name_draft(nome).
        """

        self.source_table_id = source_table_id
        self.source_table_schema = source_table_schema
        self.custom_name = custom_name
        self._operators: List[Operator] = []

    def add_unary_operator(self, operator: UnaryOperator) -> None:
        """Collega il nuovo operatore unario all'ultimo inserito nel Draft."""

        self.checks(operator)

        prev_op = self.get_last_operator()
        operator.set_parents([prev_op])    
        self._operators.append(operator)

    def add_binary_operator(
        self,
        operator: BinaryOperator,
        right_parent: TableRefOp,
    ) -> None:
        """
        Collega il nuovo operatore binario all'ultimo inserito nel Draft.
        Il parent destro deve essere un TableRefOp.
        """

        self.checks(operator)

        left_op = self.get_last_operator()
        operator.set_parents([left_op, right_parent])
        self._operators.append(operator)
        
    def get_last_operator(self) -> Operator:
        """
        Restituisce l'ultimo operatore attualmente presente nel Draft.
        Se non ci sono operatori rende il TableRefOp alla tabella madre.
        """

        if len(self._operators) == 0:
            self._operators.append(TableRefOp(self.source_table_id, self.source_table_schema))

        return self._operators[-1]

    def checks(self, current_op: Operator) -> None:
        """
        Controlla che valgano le condizioni di seguenza degli operatori,
         se tale non è il caso solleva un RuntimeError.
        """
        prev_op = self.get_last_operator()

        if (not isinstance(current_op, SelectOp)) and isinstance(prev_op, GroupByOp):
            raise RuntimeError(
                f"Operazione non valida: non è possibile applicare '{current_op.get_op_type()}' dopo un GroupBy. "
                f"Dopo group_by() è obbligatorio invocare select() per definire proiezioni ed aggregazioni."
            )

    def handle_group(self, selections: List[Expression]) -> List[Expression]:
        """
        Modifica lo schema del GroupByOp con le aggregazioni presenti nella select successiva.
        Rende le selezioni compatibili.
        """

        #ricavo il group by e varie sue info
        prev_op = self.get_last_operator()
        if not isinstance(prev_op, GroupByOp):
            raise RuntimeError(f"Errore di drafting {prev_op} non è un GroupByOp.")
        
        old_schema = prev_op.input_schema
        group_keys = prev_op.keys

        #validazione delle selezioni
        for expr in selections:
            if not expr.validate_grouped(group_keys):
                raise ValueError(
                    f"L'espressione {expr} non è valida a seguito di un"
                    f" group_by({group_keys})"
                )

        #dipendenze delle aggregazioni
        aggregations_map: Dict[str, AggregateExpression] = {}
        for expr in selections:
            for agg in expr.aggregation_dependencies():
                sig = agg.get_default_name()
                if sig not in aggregations_map:
                    aggregations_map[sig] = agg

        #schema del group_by
        group_schema_builder = SchemaBuilder()
        for k in group_keys:
            group_schema_builder.add_column(k, old_schema.get_type_for(k))
        for agg in aggregations_map.values():
            group_schema_builder.add_expression(agg, old_schema, default_name=True)

        prev_op._schema_out = group_schema_builder.build()
        prev_op.aggregations = list(aggregations_map.values())

        #riscrittura delle selezioni
        return [e.rewrite_grouped() for e in selections]

        
    @property
    def current_schema(self) -> Schema:
        """
        Restituisce lo schema di output dell'ultimo operatore inserito nel Draft, ovvero
        lo schema che riceverà in input il prossimo operatore inserito.
        """
        return self.get_last_operator().schema_out
  