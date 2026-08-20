from windflow_table_api import *
from pathlib import Path

gen = SchemaGenerator()
par = JsonParser(Path("./output"))
etl = ExpressionTranslator()

gra = par.parse_query("q1_q2_join")

def post_visit(root: OpNode):
    for p in root.parents:
        post_visit(p)  

    if root.raw_dict["op_type"] == "SELECT":
        for e in root.raw_dict["expressions"]:
            print(etl.translate_expr(e))

    if root.raw_dict["op_type"] == "WHERE":
        print(etl.translate_expr(root.raw_dict["condition"]))
             
post_visit(gra.target_root)

#test su funzioni d'aggregazione
aggregations = [
                    {
                        "expr_type": "AGGREGATE",
                        "func": "AVG",
                        "data_type": "DOUBLE",
                        "target": {
                            "expr_type": "COL_REF",
                            "name": "temperature",
                            "data_type": "DOUBLE"
                        },
                        "is_distinct": False,
                        "name": "AVG_temperature",
                        "alias": "avg_temp"
                    },
                    {
                        "expr_type": "AGGREGATE",
                        "func": "COUNT",
                        "data_type": "BIGINT",
                        "target": None,
                        "is_distinct": False,
                        "name": "COUNT_"
                    },
                    {
                        "expr_type": "AGGREGATE",
                        "func": "SUM",
                        "data_type": "DOUBLE",
                        "target": {
                            "expr_type": "COL_REF",
                            "name": "temperature",
                            "data_type": "DOUBLE"
                        },
                        "is_distinct": False,
                        "name": "SUM_temperature"
                    }
]

for a in aggregations:
    print(etl.translate_aggregate(a))
    