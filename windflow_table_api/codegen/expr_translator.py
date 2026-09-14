from typing import Any, Dict, Callable
from dataclasses import dataclass
from jinja2 import Environment
from .utility import OPERATOR_MAP, LITERAL_FORMATTERS
from ..object_names import ExprType, AggFuncType
from ..datatypes import DataTypes

#dati da passare alle sotto-espressioni
@dataclass(frozen=True)
class TranslationContext:
    input_var: str = "in"
    output_var: str = "out"

class ExpressionTranslator:
    """Traduce le espressioni nel JSON in stringhe di codice C++."""

    def __init__(self, env: Environment):
        self.jinja_env = env

        #dispatcher per espressioni semplici
        self._expr_dispatch: Dict[Any, Callable[[Dict[str, Any], TranslationContext], str]] = {
            ExprType.LITERAL: self._translate_literal,
            ExprType.COL_REF: self._translate_col_ref,
            ExprType.BINARY_OP: self._translate_binary_op,
            ExprType.UNARY_OP: self._translate_unary_op,
        }

        #dispatcher per aggregazioni
        self._agg_dispatch: Dict[Any, Callable[[Dict[str, Any], TranslationContext], str]] = {
            AggFuncType.COUNT: self._translate_count,
            AggFuncType.SUM: self._translate_sum,
            AggFuncType.AVG: self._translate_avg,
            AggFuncType.MAX: self._translate_max,
            AggFuncType.MIN: self._translate_min,
        }

    def translate_expr(
        self, expr_dict: Dict[str, Any], ctx:TranslationContext = TranslationContext() 
    ) -> str:
        """
        Punto di ingresso ricorsivo per la traduzione di una generica espressione.
        Instrada la chiamata al metodo corretto in base a 'expr_type'. Il parametro
        'input_var' è il nome della variabile a cui si applica l'espressione.
        """

        expr_type = expr_dict.get("expr_type")

        #ottengo il metodo da chiamare
        handler = self._expr_dispatch.get(expr_type)
        if not handler:
            raise NotImplementedError(f"Tipo espressione non supportato: '{expr_type}'")

        return handler(expr_dict, ctx)

    def _translate_col_ref(
        self, expr_dict: Dict[str, Any], ctx:TranslationContext
    ) -> str:
        """Traduce un riferimento a colonna (COL_REF)."""

        col_name = expr_dict["name"]

        return f"{ctx.input_var}.{col_name}"

    def _translate_literal(self, expr_dict: Dict[str, Any], ctx:TranslationContext) -> str:
        """
        Traduce un valore costante letterale (LITERAL).
        Gestisce correttamente stringhe, numeri e booleani.
        """

        if "value" not in expr_dict or expr_dict["value"] is None:
            raise ValueError(f"Nodo LITERAL non valido o campo 'value' mancante: {expr_dict}")

        val = expr_dict["value"]
        data_type_raw = expr_dict.get("data_type")

        if not data_type_raw:
            raise ValueError(f"Campo 'data_type' obbligatorio mancante nel nodo LITERAL: {expr_dict}")

        #estraggo il DataType se possibile
        try:
            dtype = DataTypes(data_type_raw) if isinstance(data_type_raw, str) else data_type_raw
        except ValueError:
            raise NotImplementedError(f"Tipo dato sconosciuto o non censito: '{data_type_raw}'")

        formatter = LITERAL_FORMATTERS.get(dtype)
        if not formatter:
            raise NotImplementedError(f"Nessun formattatore C++ definito per il tipo '{dtype}'")

        return formatter(val)

    def _translate_binary_op(
      self, expr_dict: Dict[str, Any], ctx:TranslationContext
    ) -> str:
        """Traduce ricorsivamente un'operazione binaria (BINARY_OP)."""

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore binario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        # tarduzione ricorsiva
        left_cpp = self.translate_expr(expr_dict["left"], ctx)
        right_cpp = self.translate_expr(expr_dict["right"], ctx)

        return f"({left_cpp} {cpp_op} {right_cpp})"

    def _translate_unary_op(
      self, expr_dict: Dict[str, Any], ctx:TranslationContext
    ) -> str:
        """Traduce un'operazione unaria (UNARY_OP), come la negazione logica '!'."""

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore unario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        inner_expr = expr_dict.get("expr")
        if inner_expr is None:
            raise KeyError("Manca il sotto-albero dell'espressione unaria.")

        inner_cpp = self.translate_expr(inner_expr, ctx)

        return f"{cpp_op}{inner_cpp}"

# -------------------------------------------------------------------------
# Aggregazioni
# -------------------------------------------------------------------------

    def translate_aggregate(
      self,
      agg_dict: Dict[str, Any],
      ctx:TranslationContext = TranslationContext()
    ) -> str:
        """Rende l'accumulatore per il GroupBy."""

        agg_type = agg_dict["func"]

        handler = self._agg_dispatch.get(agg_type)
        if not handler:
            raise NotImplementedError(f"Funzione di aggregazione non supportata: '{agg_type}'")

        return handler(agg_dict, ctx)

    def _translate_count(self, expr_dict: Dict[str, Any], ctx:TranslationContext) -> str:
        template = self.jinja_env.get_template("aggregates/count.jinja2")
        return template.render(
            field= expr_dict["name"],
            out_var= ctx.output_var
        ) 

    def _translate_sum(self, 
        expr_dict: Dict[str, Any], 
        ctx: TranslationContext
        ) -> str:
        target = expr_dict["target"]
        target_cpp = self.translate_expr(target, ctx)

        template = self.jinja_env.get_template("aggregates/sum.jinja2")
        return template.render(
            field= expr_dict["name"],
            out_var= ctx.output_var,
            target= target_cpp
        )       

    def _translate_max(self, 
        expr_dict: Dict[str, Any], 
        ctx: TranslationContext
        ) -> str:
        target = expr_dict["target"]
        target_cpp = self.translate_expr(target, ctx)

        template = self.jinja_env.get_template("aggregates/max.jinja2")
        return template.render(
            field= expr_dict["name"],
            out_var= ctx.output_var,
            target= target_cpp
        )         

    def _translate_min(self, 
        expr_dict: Dict[str, Any], 
        ctx: TranslationContext
        ) -> str:
        target = expr_dict["target"]
        target_cpp = self.translate_expr(target, ctx)

        template = self.jinja_env.get_template("aggregates/min.jinja2")
        return template.render(
            field= expr_dict["name"],
            out_var= ctx.output_var,
            target= target_cpp
        ) 
          
    def _translate_avg(self, 
        expr_dict: Dict[str, Any], 
        ctx: TranslationContext
        ) -> str:
        target = expr_dict["target"]

        template = self.jinja_env.get_template("aggregates/avg.jinja2")
        return template.render(
            field= expr_dict["name"],
            out_var= ctx.output_var,
            target= target["name"]
        )       
   