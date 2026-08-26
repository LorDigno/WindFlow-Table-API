from windflow_table_api import *
from pathlib import Path

par = JsonParser(Path("./output"))
sch = SchemaGenerator()
etl = ExpressionTranslator()
exp = GraphExplorer(sch, etl, Path("./output"), 2)

graph = par.parse_query("q1_q2_join")
exp.visit(graph.target_root)

for b in exp.builders:
    print(b + "\n")
for p in exp.pipes:
    print(exp.pipes[p] + ";\n")    
