from pathlib import Path
from typing import Union, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from .parser import JsonParser, ParsedGraph, OpNode
from .schema_gen import SchemaGenerator
from .expr_translator import ExpressionTranslator
from .explorer import GraphExplorer
from ..times import TimeFormats

def generate_code(
    query_id: str,
    time_policy: str = "NO_POLICY",
    parallelism: int = 1,
    json_dir: Union[Path, str] = Path("."),
    epoch: Optional[Tuple[str, TimeFormats]] = None
) -> None:
    json_dir = Path(json_dir)

    #parsing del json
    parser = JsonParser(json_dir=json_dir)
    parsed_graph = parser.create_ast(query_id)

    #setup di jinja
    templates_dir = Path(__file__).parent / "templates" 
    jinja_env = Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )

    #nome della variabile di epoch se necessaria
    epoch_var = f"{query_id}_epoch" if epoch else None

    #esplorazione del grafo
    explorer = GraphExplorer( jinja_env, json_dir, parallelism, epoch_var)
    explorer.visit(parsed_graph.target_root)

    #scrive l'header degli struct
    explorer.sch_gen.write_header_file(json_dir , query_id)

    #generazione del main
    template = jinja_env.get_template("main.cpp.jinja2")
    main_string = template.render(
        query_id= query_id,
        builders= explorer.builders,
        policy= time_policy if time_policy != "NO_POLICY" else None,
        pipe_order= explorer.pipe_order,
        pipes= explorer.pipes,
        #gestion epoch
        epoch_var= epoch_var,
        epoch_str= epoch[0] if epoch else None,
        epoch_format= epoch[1].value if epoch else None
    )

    #scrittura del file
    file_path = json_dir / f"{query_id}_main.cpp"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(main_string)
