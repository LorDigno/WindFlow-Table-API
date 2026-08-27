from windflow_table_api import *
from pathlib import Path

par = JsonParser(Path("./output"))
sch = SchemaGenerator()
etl = ExpressionTranslator()
exp = GraphExplorer(sch, etl, Path("./output"), 1)

graph = par.parse_query("q1_q2_join")
exp.visit(graph.target_root)

print("------ \t STRUCTS: \n")
print(sch.render_all_structs("q1_q2_join") + "\n\n")

print("------ \t BUILDERS: \n")
for b in exp.builders:
    print(b + "\n")

print("------ \t PIPES: \n")    
for p in exp.pipes:
    print(exp.pipes[p] + ";\n")    
