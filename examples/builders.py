from windflow_table_api import *
from pathlib import Path

par = JsonParser(Path("./output"))
sch = SchemaGenerator()
etl = ExpressionTranslator()
exp = GraphExplorer(sch, etl, Path("./output"), 1)

graph = par.parse_query("q1_q2_join")
exp.visit(graph.target_root)

#attualmente la pipe non viene mai istanziata dunque da errore ma istanziandola forzatamente fa
print(exp.pipes)
print(exp.builders)

#output:
#{'pipe_1': '.add(where_1_op)'}
#['auto where_1_op = Where_Builder<sensor_q1_where_5_struct>(\n
#         [](const sensor_q1_where_5_struct& in) -> bool {
# \n    return (((in.humidity > 20) && (in.temperature > 20)) && (in.temperature < 30));\n}
# \n    )\n
#     .withName("where_sensor_q1_where_5")\n    
#      .withParallelism(1)\n    
# .build();']