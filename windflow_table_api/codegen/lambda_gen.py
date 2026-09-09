from typing import Dict, List, Tuple, Any, Tuple
from jinja2 import Environment

class LambdaGenerator:
    """
    Offre i metodi per renderizzare i template Jinja per i vari tipi di lambda.
    L'ambiente di input si richiede che sia inizializzato a codegen/templates/ .
    """

    def __init__(self, env: Environment):
        self._jinja_env = env

    def map_lambda(
        self,
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        input_var: str = "in"
    ) -> str:
        template = self._jinja_env.get_template( "lambdas/map_lambda.jinja2")
        return template.render(
            input_struct=in_struct,
            output_struct=out_struct,
            mappings=mappings,
            input_var= input_var
        )

    def where_lambda(
        self,
        in_struct: str,
        condition: str,
        in_var: str = "in"
    ) -> str:
        template = self._jinja_env.get_template("lambdas/where_lambda.jinja2")
        return template.render(
            input_struct=in_struct,
            condition=condition,
            input_var= in_var
        )

    def groupBy_lambda(
        self,
        in_struct: str,
        out_struct: str,
        keys: List[str],
        accumulations: List[str], 
        in_var: str = "in",
        out_var: str = "out"
    ) -> str:
        template = self._jinja_env.get_template("lambdas/group_lambda.jinja2")
        return template.render(
            input_struct=in_struct,
            output_struct= out_struct,
            keys= keys,
            accumulations= accumulations, 
            input_var= in_var,
            output_var= out_var
        )

    def join_lambda(
        self,
        input_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        left_var: str = "left",
        right_var: str = "right",
    ) -> str:
        template = self._jinja_env.get_template("lambdas/join_lambda.jinja2")
        return template.render(
            input_struct=input_struct,
            output_struct= out_struct,
            mappings= mappings, 
            left_var= left_var,
            right_var= right_var
        )        

    def parser_lambda(
        self,
        struct_out: str,
        time_col_dict: Dict[str, Any],
        ordered_fields: List[Dict[str, Any]]
    ) -> str:
        template = self._jinja_env.get_template("lambdas/parser_lambda.jinja2")
        return template.render(
            out_struct=struct_out,
            time_col=time_col_dict,
            fields=ordered_fields
        )

    def sink_lambda(
        self,
        in_struct: str,
        fields: Dict[str, str]
    ) -> str:
        template = self._jinja_env.get_template("lambdas/sink_lambda.jinja2")
        return template.render(
            in_struct=in_struct,
            fields=fields
        )
    