import argparse
from pathlib import Path
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
    explorer = GraphExplorer(s_gen, e_tl, args.output_dir)
    explorer.visit(parsed_graph.target_root)
      

if __name__ == "__main__":
    main()

