from pathlib import Path
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from .utility import OPERATOR_MAP, TYPE_MAP


class ExpressionTranslator:
    """Traduce le espressioni nel JSON in stringhe di codice C++."""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates" / "expressions"

        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def translate_expr(
        self, expr_dict: Dict[str, Any], input_var: str = "in"
    ) -> str:
        """
        Punto di ingresso ricorsivo per la traduzione di una generica espressione.
        Instrada la chiamata al metodo corretto in base a 'expr_type'. Il parametro
        'input_var' è il nome della variabile a cui si applica l'espressione.
        """

        expr_type = expr_dict.get("expr_type")

        if expr_type == "LITERAL":
            return self._translate_literal(expr_dict)
        elif expr_type == "COL_REF":
            return self._translate_col_ref(expr_dict, input_var)
        elif expr_type == "UNARY_OP":
            return self._translate_unary_op(expr_dict, input_var)
        elif expr_type == "BINARY_OP":
            return self._translate_binary_op(expr_dict, input_var)
        else:
            raise ValueError(
                f"Tipo di espressione non supportato o non riconosciuto: '{expr_type}'"
            )

    def _translate_col_ref(
        self, expr_dict: Dict[str, Any], input_var: str = "in"
    ) -> str:
        """Traduce un riferimento a colonna (COL_REF)."""

        col_name = expr_dict["name"]

        template = self.jinja_env.get_template("col_ref.jinja2")
        return template.render(
        input_var= input_var,
        col_name= col_name
        )

    def _translate_literal(self, expr_dict: Dict[str, Any]) -> str:
        """
        Traduce un valore costante letterale (LITERAL).
        Gestisce correttamente stringhe, numeri e booleani.
        """

        if "value" not in expr_dict or expr_dict["value"] is None:
            raise ValueError(
                f"Nodo LITERAL non valido o campo 'value' mancante: {expr_dict}"
            )

        val = expr_dict["value"]
        data_type = expr_dict.get("data_type")

        if data_type == "BOOLEAN" or isinstance(val, bool):
            return "true" if val else "false"

        if data_type == "STRING" or isinstance(val, str):
            return f'std::string("{val}")'

        if data_type == "FLOAT":
            return f"{float(val)}f"

        if data_type == "DOUBLE" or isinstance(val, float):
            return str(float(val))

        if data_type == "BIGINT":
            return f"{int(val)}LL"

        if data_type == "INT" or isinstance(val, int):
            return str(int(val))

        raise ValueError(f"Tipo di letterale {data_type} sconosciuto.")

    def _translate_binary_op(
      self, expr_dict: Dict[str, Any], input_var: str = "in"
    ) -> str:
        """Traduce ricorsivamente un'operazione binaria (BINARY_OP)."""

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore binario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        # tarduzione ricorsiva
        left_cpp = self.translate_expr(expr_dict["left"], input_var)
        right_cpp = self.translate_expr(expr_dict["right"], input_var)

        template = self.jinja_env.get_template("bin_op.jinja2")
        return template.render(
            left= left_cpp,
            op= cpp_op,
            right= right_cpp
        )

    def _translate_unary_op(
      self, expr_dict: Dict[str, Any], input_var: str = "in"
    ) -> str:
        """Traduce un'operazione unaria (UNARY_OP), come la negazione logica '!'."""

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore unario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        inner_expr = expr_dict.get("expr")
        if inner_expr is None:
            raise KeyError("Manca il sotto-albero dell'espressione unaria.")

        inner_cpp = self.translate_expr(inner_expr, input_var)

        template = self.jinja_env.get_template("un_op.jinja2")
        return template.render(
            op= cpp_op,
            inner= inner_cpp
        )

# -------------------------------------------------------------------------
# Aggregazioni
# -------------------------------------------------------------------------

    def translate_aggregate(
      self,
      expr_dict: Dict[str, Any],
      input_var: str = "in",
      output_var: str = "out",
    ) -> str:
        """Rende l'accumulatore per il GroupBy."""

        agg_type = expr_dict["func"]

        if agg_type == "COUNT":
            return self._translate_count(expr_dict, output_var)
        elif agg_type == "SUM":
            return self._translate_sum(expr_dict, input_var, output_var)
        elif agg_type == "MAX":
            return self._translate_max(expr_dict, input_var, output_var)
        elif agg_type == "MIN":
            return self._translate_min(expr_dict, input_var, output_var)
        elif agg_type == "AVG":
            return self._translate_avg(expr_dict, input_var, output_var)
        return ""

    def _translate_count(self, expr_dict: Dict[str, Any], output_var: str = "out") -> str:
        target = expr_dict["target"]

        if not expr_dict.get("distinct") or target == None:
            #count semplice
            template = self.jinja_env.get_template("count.jinja2")
            return template.render(
                field= expr_dict["name"],
                out_var= output_var
            ) 

        return ""

    def _translate_sum(self, 
        expr_dict: Dict[str, Any], 
        input_var:str = "in", 
        output_var: str = "out"
        ) -> str:
        target = expr_dict["target"]

        if not expr_dict.get("distinct"):
            #sum semplice

            target_cpp = self.translate_expr(target, input_var)

            template = self.jinja_env.get_template("sum.jinja2")
            return template.render(
                field= expr_dict["name"],
                out_var= output_var,
                target= target_cpp
            )       

        return ""  

    def _translate_max(self, 
        expr_dict: Dict[str, Any], 
        input_var:str = "in", 
        output_var: str = "out"
        ) -> str:
        target = expr_dict["target"]

        if not expr_dict.get("distinct"):
            #max semplice

            target_cpp = self.translate_expr(target, input_var)

            template = self.jinja_env.get_template("max.jinja2")
            return template.render(
                field= expr_dict["name"],
                out_var= output_var,
                target= target_cpp
            )       

        return ""    

    def _translate_min(self, 
        expr_dict: Dict[str, Any], 
        input_var:str = "in", 
        output_var: str = "out"
        ) -> str:
        target = expr_dict["target"]

        if not expr_dict.get("distinct"):
            #min semplice

            target_cpp = self.translate_expr(target, input_var)

            template = self.jinja_env.get_template("min.jinja2")
            return template.render(
                field= expr_dict["name"],
                out_var= output_var,
                target= target_cpp
            )       

        return ""        

    def _translate_avg(self, 
        expr_dict: Dict[str, Any], 
        input_var:str = "in", 
        output_var: str = "out"
        ) -> str:
        target = expr_dict["target"]

        if not expr_dict.get("distinct"):
            #avg semplice

            template = self.jinja_env.get_template("avg.jinja2")
            return template.render(
                field= expr_dict["name"],
                out_var= output_var,
                target= target["name"]
            )       

        return ""   