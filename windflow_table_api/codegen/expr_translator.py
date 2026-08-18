from typing import Dict, List, Any, Optional
from .utility import OPERATOR_MAP

class ExpressionTranslator:
    """
    Traduce le espressioni nel JSON in stringhe di codice C++. 
    """

    @staticmethod
    def translate_expr(expr_dict: Dict[str, Any], input_var: str = "in") -> str:
        """
        Punto di ingresso ricorsivo per la traduzione di una generica espressione.
        Instrada la chiamata al metodo corretto in base a 'expr_type'.
        Il parametro 'input_var' è il nome della variabile a cui si applica l'espressione.
        """

        expr_type = expr_dict.get("expr_type")

        if expr_type == "LITERAL":
            return ExpressionTranslator._translate_literal(expr_dict)
        elif expr_type == "COL_REF":
            return ExpressionTranslator._translate_col_ref(expr_dict, input_var)
        elif expr_type == "UNARY_OP":
            return ExpressionTranslator._translate_unary_op(expr_dict, input_var)
        elif expr_type == "BINARY_OP":
            return ExpressionTranslator._translate_binary_op(expr_dict, input_var)
        else:
            raise ValueError(f"Tipo di espressione non supportato o non riconosciuto: '{expr_type}'")

    @staticmethod
    def _translate_col_ref(expr_dict: Dict[str, Any], input_var: str = "in") -> str:
        """
        Traduce un riferimento a colonna (COL_REF).
        """

        col_name = expr_dict["name"]
        return f"{input_var}.{col_name}"

    @staticmethod
    def _translate_literal(expr_dict: Dict[str, Any]) -> str:
        """
        Traduce un valore costante letterale (LITERAL).
        Gestisce correttamente stringhe, numeri e booleani.
        """

        if "value" not in expr_dict or expr_dict["value"] is None:
            raise ValueError(f"Nodo LITERAL non valido o campo 'value' mancante: {expr_dict}")

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

        return str(val)

    @staticmethod
    def _translate_binary_op(expr_dict: Dict[str, Any], input_var: str = "in") -> str:
        """
        Traduce ricorsivamente un'operazione binaria (BINARY_OP).
        """

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore binario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        #tarduzione ricorsiva
        left_cpp = ExpressionTranslator.translate_expr(expr_dict["left"], input_var)
        right_cpp = ExpressionTranslator.translate_expr(expr_dict["right"], input_var)

        return f"({left_cpp} {cpp_op} {right_cpp})"

    @staticmethod
    def _translate_unary_op(expr_dict: Dict[str, Any], input_var: str = "in") -> str:
        """
        Traduce un'operazione unaria (UNARY_OP), come la negazione logica '!'.
        """

        raw_op = expr_dict["op"]
        if raw_op not in OPERATOR_MAP:
            raise KeyError(f"Operatore unario non supportato: '{raw_op}'")

        cpp_op = OPERATOR_MAP[raw_op]

        inner_expr = expr_dict.get("expr")
        if inner_expr is None:
            raise KeyError("Manca il sotto-albero dell'espressione unaria.")

        inner_cpp = ExpressionTranslator.translate_expr(inner_expr, input_var)

        return f"{cpp_op}({inner_cpp})"
    