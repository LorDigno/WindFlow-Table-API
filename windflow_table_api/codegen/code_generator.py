from pathlib import Path
from typing import Union
from jinja2 import Environment, FileSystemLoader
from .parser import JsonParser, ParsedGraph, OpNode
from .schema_gen import SchemaGenerator
from .expr_translator import ExpressionTranslator
from .explorer import GraphExplorer

def generate_code(
    query_id: str,
    time_policy: str = "NO_POLICY",
    parallelism: int = 1,
    json_dir: Union[Path, str] = Path("."),
) -> None:
    json_dir = Path(json_dir)

    #parsing del json
    parser = JsonParser(json_dir=json_dir)
    parsed_graph = parser.parse_query(query_id)

    #creazione degli oggetti di traduzione
    s_gen = SchemaGenerator()
    e_tl = ExpressionTranslator()

    #esplorazione del grafo
    explorer = GraphExplorer(s_gen, e_tl, json_dir, parallelism)
    final_struct = explorer.visit(parsed_graph.target_root)
    explorer.add_sink(
        filepath= f"{query_id}",
        final_struct= final_struct,
        sink_name= f"{query_id}_sink"
    )

    #scrive l'header degli struct
    s_gen.write_header_file(json_dir , query_id)

    #setup di jinja
    templates_dir = Path(__file__).parent / "templates" 
    jinja_env = Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )

    #generazione del main
    template = jinja_env.get_template("main.cpp.jinja2")
    main_string = template.render(
        query_id= query_id,
        builders= explorer.builders,
        policy= time_policy if time_policy != "NO_POLICY" else None,
        pipe_order= explorer.pipe_order,
        pipes= explorer.pipes
    )

    #scrittura del file
    file_path = json_dir / f"{query_id}_main.cpp"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(main_string)
