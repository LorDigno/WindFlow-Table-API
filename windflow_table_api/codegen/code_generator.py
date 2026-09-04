import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .parser import JsonParser, ParsedGraph, OpNode
from .schema_gen import SchemaGenerator
from .expr_translator import ExpressionTranslator
from .explorer import GraphExplorer

def main():
    cli_parser = argparse.ArgumentParser(
        description="WindFlow Table API - Code Generator Entrypoint"
    )

    cli_parser.add_argument(
        "query_id", 
        type=str, 
        help="ID della query target da parsare"
    )

    cli_parser.add_argument(
        "--time-policy",
        type=str,
        default="NO_POLICY",
        choices=["NO_POLICY", "INGRESS_TIME", "EVENT_TIME"],
        help="Politica temporale (default: NO_POLICY)"
    )

    cli_parser.add_argument(
        "-p", "--parallelism",
        type=int,
        default=1,
        help="Grado di parallelismo di default per gli operatori (default: 1)"
    )

    cli_parser.add_argument(
        "--json-dir",
        type=Path,
        default=Path("."),
        help="Directory contenente i file JSON dell'AST (default: .)"
    )

    args = cli_parser.parse_args()

    #parsing del json
    parser = JsonParser(json_dir=args.json_dir)
    parsed_graph = parser.parse_query(args.query_id)

    #creazione degli oggetti di traduzione
    s_gen = SchemaGenerator()
    e_tl = ExpressionTranslator()

    #esplorazione del grafo
    explorer = GraphExplorer(s_gen, e_tl, args.json_dir, args.parallelism)
    final_struct = explorer.visit(parsed_graph.target_root)
    explorer.add_sink(
        filepath= f"{args.query_id}_output.csv",
        final_struct= final_struct,
        sink_name= f"{args.query_id}_sink"
    )

    #scrive l'header degli struct
    s_gen.write_header_file(args.json_dir , args.query_id)

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
        query_id= args.query_id,
        builders= explorer.builders,
        policy= args.time_policy if args.time_policy != "NO_POLICY" else None,
        pipe_order= explorer.pipe_order,
        pipes= explorer.pipes
    )

    #scrittura del file
    file_path = args.json_dir / f"{args.query_id}_main.cpp"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(main_string) 

if __name__ == "__main__":
    main()

