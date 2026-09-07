from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union, Dict, List
from ..datatypes import DataTypes
from windflow_table_api import ExprType, AggFuncType
import copy
if TYPE_CHECKING:
    from .schema import Schema

def _infer_literal_type(val: Any) -> DataTypes:
    """Inferisce il DataType a partire da un valore nativo Python."""

    if isinstance(val, bool):
        return DataTypes.BOOLEAN
    elif isinstance(val, int):
        return DataTypes.INT
    elif isinstance(val, float):
        return DataTypes.DOUBLE
    elif isinstance(val, str):
        return DataTypes.STRING
    else:
        raise TypeError(f"Impossibile inferire il DataType per il valore {val} ({type(val)})")

class Expression(ABC):
    """
    Classe base per qualsiasi espressione della Table API.
    """

    def __init__(self):
        self._alias_name: Optional[str] = None

    def alias(self, alias_name: str) -> "Expression":
        """
        Crea una shallow-copy ed assegna un nuovo nome di output all'espressione.
        """

        new_expr = copy.copy(self)
        new_expr._alias_name = alias_name
        return new_expr

    @abstractmethod
    def get_expr_type(self) -> ExprType:
        """Restituisce il tipo logico dell'espressione."""
        pass

    @abstractmethod
    def get_default_name(self) -> str:
        """Restituisce il nome predefinito se non è stato impostato un alias."""
        pass

    def get_name(self) -> str:
        """Restituisce l'alias se presente, altrimenti il nome predefinito."""

        return self._alias_name if self._alias_name is not None else self.get_default_name()

    @abstractmethod
    def get_type(self, schema: Schema) -> DataTypes:
        """
        Calcola e restituisce il DataType risultante applicando 
        l'espressione sullo schema di input.
        """
        pass

    @abstractmethod
    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_grouped(self, keys: List[str]) -> bool:
        """Controlla che questa espressione possa essere selezionata a seguito di un group_by(keys)."""
        pass

    @abstractmethod
    def aggregation_dependencies(self) -> List[AggregateExpression]:
        """Rende le aggregazioni che è necessario calcolare per valutare l'espressione."""
        pass

    @abstractmethod
    def rewrite_grouped(self) -> "Expression":
        """Riscrive l'espressione affinché faccia riferimento ai campi generati dallo schema del GroupByOp."""
        pass

    def _to_expr(self, other: Any) -> "Expression":
        """Converte un valore scalare in una LiteralExpression se necessario."""

        if isinstance(other, Expression):
            return other
        return lit(other)

    # -------------------------------------------------------------------------
    # Overloading degli operatori algebrici e logici
    # -------------------------------------------------------------------------

    def __add__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "+", self._to_expr(other))

    def __sub__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "-", self._to_expr(other))

    def __mul__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "*", self._to_expr(other))

    def __truediv__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "/", self._to_expr(other))

    def __gt__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, ">", self._to_expr(other))

    def __lt__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "<", self._to_expr(other))

    def __ge__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, ">=", self._to_expr(other))

    def __le__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "<=", self._to_expr(other))

    def __eq__(self, other: Any) -> "BinaryOpExpression":  
        return BinaryOpExpression(self, "==", self._to_expr(other))

    def __ne__(self, other: Any) -> "BinaryOpExpression":  
        return BinaryOpExpression(self, "!=", self._to_expr(other))

    def __and__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "&&", self._to_expr(other))

    def __or__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "||", self._to_expr(other))

    def __invert__(self) -> UnaryOpExpression:
        """
        Bitwise Not (~) usato per il not logico perché il not logico non ha un metodo magico.
        """
        return UnaryOpExpression(self, "not")

# -------------------------------------------------------------------------
# Classi figlie di Expression
# -------------------------------------------------------------------------

class ColRefExpression(Expression):
    """Riferimento a una colonna esistente nello Schema."""

    def __init__(self, column_name: str):
        super().__init__()
        self.column_name = column_name

    def get_expr_type(self) -> ExprType:
        return ExprType.COL_REF

    def get_default_name(self) -> str:
        return self.column_name

    def get_type(self, schema: Schema) -> DataTypes:
        return schema.get_type_for(self.column_name)

    def __repr__(self) -> str:
        alias_str = f" AS '{self._alias_name}'" if self._alias_name else ""
        return f"col('{self.column_name}'){alias_str}"

    def to_dict(self, applied_schema:Schema) -> Dict[str, Any]:
        res = {
            "expr_type": self.get_expr_type().value,
            "name": self.column_name,
            "data_type": self.get_type(applied_schema).name
        }
        if self._alias_name:
            res["alias"] = self._alias_name
        return res

    def validate_grouped(self, keys: List[str]) -> bool:
        #si possono selezionare solo le colonne chiave
        return self.column_name in keys

    def aggregation_dependencies(self) -> List[AggregateExpression]:
        return []

    def rewrite_grouped(self) -> Expression:
        return self    

class LiteralExpression(Expression):
    """Rappresenta una costante con relativo DataType."""

    def __init__(self, value: Any, data_type: Optional[DataTypes] = None):
        super().__init__()
        self.value = value
        self.data_type = data_type if data_type is not None else _infer_literal_type(value)

    def get_expr_type(self) -> ExprType:
        return ExprType.LITERAL

    def get_default_name(self) -> str:
        return str(self.value)

    def get_type(self, schema: Schema) -> DataTypes:
        return self.data_type

    def __repr__(self) -> str:
        alias_str = f" AS '{self._alias_name}'" if self._alias_name else ""
        return f"lit({self.value}: {self.data_type.name}){alias_str}"

    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        res = {
            "expr_type": self.get_expr_type().value,
            "value": self.value,
            "data_type": self.data_type.name,
            "name": self.get_default_name()
        }
        if self._alias_name:
            res["alias"] = self._alias_name
        return res

    def validate_grouped(self, keys: List[str]) -> bool:
            #si può sempre avere un Literal in più
            return True

    def aggregation_dependencies(self) -> List[AggregateExpression]:
            return []

    def rewrite_grouped(self) -> Expression:
        return self

class BinaryOpExpression(Expression):
    """Rappresenta un'operazione binaria tra due espressioni."""

    def __init__(self, left: Expression, op: str, right: Expression):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def get_expr_type(self) -> ExprType:
        return ExprType.BINARY_OP  

    def get_default_name(self) -> str:
        return f"({self.left.get_name()}_{self.op}_{self.right.get_name()})"

    def get_type(self, schema: Schema) -> DataTypes:
        t_left = self.left.get_type(schema)
        t_right = self.right.get_type(schema)

        #operatori di confronto
        if self.op in (">", "<", ">=", "<=", "==", "!="):
            if (t_left != t_right) and (not(t_left.is_number() and t_right.is_number())):
                raise TypeError(
                    f"Non si può fare {t_left} {self.op} {t_right}."
                    f"I tipi devono essere lo stesso o entrambi numerici."
                )
            return DataTypes.BOOLEAN

        #operatori logici
        if self.op in ("&&", "||"):
            if not(t_left.is_bool() and t_right.is_bool()):
                raise TypeError(
                    f"Non si può fare {t_left} {self.op} {t_right}."
                    f"I tipi devono essere entrambi booleani."
                )
            return DataTypes.BOOLEAN

        #operatori aritmetici
        if self.op in ("+", "-", "*", "/"):
            return DataTypes.most_general_number(t_left, t_right)

        #non dovrebbe mai arrivarci dato che gli if devono essere comprensivi
        return t_left

    def __repr__(self) -> str:
        alias_str = f" AS '{self._alias_name}'" if self._alias_name else ""
        return f"({self.left!r} {self.op} {self.right!r}){alias_str}"
    
    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        res = {
            "expr_type": self.get_expr_type().value,
            "op": self.op,
            "data_type": self.get_type(applied_schema).name,
            "left": self.left.to_dict(applied_schema),
            "right": self.right.to_dict(applied_schema),
            "name": self.get_default_name()
        }
        if self._alias_name:
            res["alias"] = self._alias_name
        return res

    def validate_grouped(self, keys: List[str]) -> bool:
            #valida solo se sono valide le sue sotto-espressioni
            return self.left.validate_grouped(keys) and self.right.validate_grouped(keys)

    def aggregation_dependencies(self) -> List[AggregateExpression]:
        out = []
        out += self.left.aggregation_dependencies()
        out += self.right.aggregation_dependencies()
        return out  

    def rewrite_grouped(self) -> Expression:
        res = BinaryOpExpression(
            self.left.rewrite_grouped(), self.op, self.right.rewrite_grouped()
        )
        if self._alias_name:
            res = res.alias(self._alias_name)
        return res

class UnaryOpExpression(Expression):
    """Rappresenta un'operazione unaria su un'espressione."""

    def __init__(self, expr:Expression, op:str):
        super().__init__()
        self.op = op
        self.expr = expr

    def get_expr_type(self) -> ExprType:
        return ExprType.UNARY_OP    

    def get_default_name(self) -> str:
            return f"{self.op}_({self.expr.get_name()})"   

    def get_type(self, schema: Schema) -> DataTypes:
        expr_t :DataTypes = self.expr.get_type(schema)

        if self.op in ("not"):
            if expr_t != DataTypes.BOOLEAN:
                raise TypeError(
                    f"Non si può fare {self.op} {expr_t}."
                    f"Il tipo dell'espressione deve essere bool."
                )

            return DataTypes.BOOLEAN

        return expr_t

    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        res = {
            "expr_type": self.get_expr_type().value,
            "op": self.op,
            "data_type": self.get_type(applied_schema).name,
            "expr": self.expr.to_dict(applied_schema),
            "name": self.get_default_name()
        }
        if self._alias_name:
            res["alias"] = self._alias_name
        return res

    def rewrite_grouped(self) -> Expression:
        res = UnaryOpExpression(self.expr.rewrite_grouped(), self.op)
        if self._alias_name:
            res = res.alias(self._alias_name)
        return res

    def validate_grouped(self, keys: List[str]) -> bool:
        #valida solo se è valide le sotto-espressione
        return self.expr.validate_grouped(keys)

    def aggregation_dependencies(self) -> List[AggregateExpression]:
        return self.expr.aggregation_dependencies()

    def __repr__(self) -> str:
        alias_str = f" AS '{self._alias_name}'" if self._alias_name else ""
        return f"{self.op.upper()}({self.expr!r}){alias_str}"

# -------------------------------------------------------------------------
# Aggregazioni
# -------------------------------------------------------------------------

class AggregateExpression(Expression):
    """
    Rappresenta una funzione di aggregazione come SUM o COUNT.
    Viene calcolata all'interno di raggruppamenti (group_by) o globalmente.
    Nel secondo caso nella select possono esserci altri campi.
    """

    def __init__(
        self,
        func_type: AggFuncType,
        target_expr: Optional[Expression] = None
    ) -> None:
        super().__init__()
        self.func_type = func_type
        self.target_expr = target_expr

    def get_expr_type(self) -> ExprType:
        return ExprType.AGGREGATE   

    def get_default_name(self) -> str:
        if self.target_expr is None:    #per il COUNT
            return self.func_type.value  
        return f"{self.func_type.value}_{self.target_expr.get_name()}"

    def get_type(self, schema: Schema) -> DataTypes:
        #COUNT rende un BIGINT perchè il numero di tuple è potenzialmente infinito
        if self.func_type == AggFuncType.COUNT:
            return DataTypes.BIGINT

        if self.target_expr is None:
            raise ValueError(f"L'aggregazione {self.func_type.value} richiede un'espressione target.")

        #calcola il tipo reso applicando lo schema all'espressione target
        input_type = self.target_expr.get_type(schema)

        #AVG rende sempre un DOUBLE
        if self.func_type == AggFuncType.AVG:
            if not input_type.is_number():
                raise TypeError(
                    f"L'aggregazione {self.func_type.value} richiede un tipo numerico, "
                    f"ricevuto: {input_type.name}"
                )
            return DataTypes.DOUBLE

        #SUM, MIN, MAX conservano il tipo numerico di input
        if self.func_type in (AggFuncType.SUM, AggFuncType.MIN, AggFuncType.MAX):
            if not input_type.is_number():
                raise TypeError(
                    f"L'aggregazione {self.func_type.value} richiede un tipo numerico, "
                    f"ricevuto: {input_type.name}"
                )
            return input_type

        #altrimenti si suppone di mantenere il tipo in input
        return input_type

    def __repr__(self) -> str:
        alias_str = f" AS '{self._alias_name}'" if self._alias_name else ""
        target_str = repr(self.target_expr) if self.target_expr else "*"
        return f"{self.func_type.value}({target_str}){alias_str}"

    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        res = {
            "expr_type": self.get_expr_type().value,
            "func": self.func_type.value,
            "data_type": self.get_type(applied_schema).name,
            "target": self.target_expr.to_dict(applied_schema) if self.target_expr else None,
            "name": self.get_default_name()
        }
        if self._alias_name:
            res["alias"] = self._alias_name
        return res

    def validate_grouped(self, keys: List[str]) -> bool:
        #il group_by serve proprio per fare le aggregazioni
        return True

    def aggregation_dependencies(self) -> List[AggregateExpression]:
        out:List[AggregateExpression] = []
        if self.func_type == AggFuncType.AVG and self.target_expr:
            out.append(count())
            s = sum(self.target_expr)
            out.append(s)
        out.append(self)    
        return out

    def rewrite_grouped(self) -> Expression:
        res = ColRefExpression(self.get_default_name())
        if self._alias_name:
            res = res.alias(self._alias_name)
        return res

# -------------------------------------------------------------------------
# Helper Functions per l'interfaccia utente
# -------------------------------------------------------------------------

def col(name: str) -> ColRefExpression:
    """Crea una ColRefExpression a partire dal nome della colonna."""

    return ColRefExpression(name)

def lit(value: Any, data_type: Optional[DataTypes] = None) -> LiteralExpression:
    """Crea una LiteralExpression per un valore costante."""

    return LiteralExpression(value, data_type)

def sum(expr: Union[str, Expression]) -> AggregateExpression:
    """Calcola la somma dei valori della colonna o espressione target."""

    if isinstance(expr, str):
        target = col(expr)
    else:
        target = expr    

    return AggregateExpression(AggFuncType.SUM, target)

def avg(expr: Union[str, Expression]) -> AggregateExpression:
    """
    Calcola la media aritmetica dei valori della colonna o espressione target, restituisce DOUBLE.
    """

    if isinstance(expr, str):
        target = col(expr)
    else:
        target = expr

    return AggregateExpression(AggFuncType.AVG, target)

def min(expr: Union[str, Expression]) -> AggregateExpression:
    """Calcola il valore minimo della colonna o espressione target."""

    if isinstance(expr, str):
        target = col(expr)
    else:
        target = expr

    return AggregateExpression(AggFuncType.MIN, target)

def max(expr: Union[str, Expression]) -> AggregateExpression:
    """Calcola il valore massimo della colonna o espressione target."""

    if isinstance(expr, str):
        target = col(expr)
    else:
        target = expr

    return AggregateExpression(AggFuncType.MAX, target)

def count() -> AggregateExpression:
    """
    Calcola il numero di record (COUNT(*)).
    """

    return AggregateExpression(AggFuncType.COUNT, None)

def neg(expr: Expression) -> UnaryOpExpression:
    """
    Helper per il not logico per evitare di usare ~.
    Rende la UnaryOpExpression con il not logico applicato all'espressione di input. 
    """
    return ~expr
