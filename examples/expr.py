from windflow_table_api import *
from pathlib import Path

gen = SchemaGenerator()
par = JsonParser(Path("./output"))

gra = par.parse_query("q1_q2_join")

def post_visit(root: OpNode):
    for p in root.parents:
        post_visit(p)  

    if root.raw_dict["op_type"] == "SELECT":
        for e in root.raw_dict["expressions"]:
            print(ExpressionTranslator.translate_expr(e))

    if root.raw_dict["op_type"] == "WHERE":
        print(ExpressionTranslator.translate_expr(root.raw_dict["condition"]))
             

post_visit(gra.target_root)
