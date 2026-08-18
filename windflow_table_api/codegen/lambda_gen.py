from typing import Dict, List, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

#inizializzazione dell'ambiente
_TEMPLATES_DIR = Path(__file__).parent / "templates" / "lambdas"
_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
)

class LambdaGenerator:
    """
    Offre vari metodi statici per renderizzare i template Jinja per i vari tipi di lambda.
    """

    @staticmethod
    def map_lambda(
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        input_var: str = "in"
    ) -> str:
        template = _ENV.get_template("map_lambda.jinja2")
        return template.render(
            input_struct=in_struct,
            output_struct=out_struct,
            mappings=mappings,
            input_var= input_var
        )

    @staticmethod
    def where_lambda(
        in_struct: str,
        condition: str,
        in_var: str = "in"
    ) -> str:
        template = _ENV.get_template("where_lambda.jinja2")
        return template.render(
            input_struct=in_struct,
            condition=condition,
            input_var= in_var
        )

    @staticmethod
    def groupBy_lambda():
        pass

    @staticmethod
    def join_lambda():
        pass

