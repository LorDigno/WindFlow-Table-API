from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
from .datatypes import DataTypes
if TYPE_CHECKING:
    from .expressions import Expression

class Field:
    """
    Rappresenta un singolo campo/colonna all'interno di uno Schema.
    Mantiene il nome logico, il DataType e l'eventuale Espressione AST che l'ha generato.
    """

    def __init__(self, name: str, data_type: DataTypes, expression: Optional[Expression] = None):
        self.name = name
        self.data_type = data_type
        self.expression = expression

    def __repr__(self) -> str:
        expr_str = f", expr={self.expression!r}" if self.expression else ""
        return f"Field(name='{self.name}', type={self.data_type.name}{expr_str})"

class Schema:
    """
    Rappresenta lo schema immutabile di uno stream.
    Conserva la mappa dei campi indicizzati per nome.
    """

    def __init__(self, fields: Dict[str, Field]):
        self._fields: Dict[str, Field] = fields.copy()

    @property
    def fields(self) -> Dict[str, DataTypes]:
        """Restituisce una mappa nome_colonna -> DataType"""

        return {name: field.data_type for name, field in self._fields.items()}

    def get_columns(self) -> List[str]:
        """Restituisce la lista dei nomi delle colonne."""

        return list(self._fields.keys())

    def get_types(self) -> List[DataTypes]:
        """Restituisce la lista ordinata dei DataType delle colonne."""

        return [field.data_type for field in self._fields.values()]

    def has_field(self, name: str) -> bool:
        """Controlla che la colonna [name] sia presente nello Schema"""

        return name in self._fields

    def get_field(self, column_name: str) -> Field:
        """
        Restituisce l'oggetto Field associato alla colonna.
        Solleva un'eccezione se tale colonna non è presente nello Schema.
        """

        if not self.has_field(column_name):
            raise RuntimeError(f"Non esiste il campo {column_name} in {self}")
        
        return self._fields[column_name]

    def get_type_for(self, column_name: str) -> DataTypes:
        """Restituisce il DataType di una specifica colonna."""

        f = self.get_field(column_name)
        return f.data_type
        
    def get_expression_for(self, column_name: str) -> Optional[Expression]:
        """
        Restituisce l'espressione associata a una colonna se presente.
        """

        f = self.get_field(column_name)
        return f.expression
    
    def __repr__(self) -> str:
        fields_str = ", ".join(f"'{k}': {v.data_type.name}" for k, v in self._fields.items())
        return f"Schema({{{fields_str}}})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Schema):
            return False

        return other.fields == self.fields

    def to_dict(self)-> Dict[str, str]:
        return {col_name: data_type.name for col_name, data_type in self.fields.items()}
    
class SchemaBuilder:
    """
    Builder fluente per la costruzione di uno Schema.
    """

    def __init__(self):
        self._fields: Dict[str, Field] = {}

    def add_column(
        self, name: str, data_type: DataTypes, expression: Optional[Expression] = None
    ) -> SchemaBuilder:
        """
        Aggiunge una colonna specificando esplicitamente nome, DataType ed eventuale espressione.
        Se la colonna è già presente solleva un errore.
        """

        if name in self._fields:
            raise ValueError(f"La colonna '{name}' è già presente nello schema {self._fields}.")
        
        self._fields[name] = Field(name, data_type, expression)
        return self

    def add_expression(self, expr: Expression, input_schema: Schema) -> SchemaBuilder:
        """
        Aggiunge una colonna derivata direttamente da un'Expression:
        - Estrae il nome dall'alias o dal nome di default dell'espressione
        - Calcola il DataType applicando l'espressione sullo schema di input
        - Associa l'oggetto Expression al campo
        """

        col_name = expr.get_name()
        col_type = expr.get_type(input_schema)
        return self.add_column(col_name, col_type, expression=expr)

    def build(self) -> Schema:
        """Finalizza lo schema costruito e lo rende."""
        return Schema(self._fields)
    