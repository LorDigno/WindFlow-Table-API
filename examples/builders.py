from windflow_table_api import *
from pathlib import Path

par = JsonParser(Path("./output"))
sch = SchemaGenerator()
etl = ExpressionTranslator()
exp = GraphExplorer(sch, etl, Path("./output"), 1)

graph = par.parse_query("q1_q2_join")
exp.visit(graph.target_root)

print(exp.pipes)
print(exp.builders)

#output, per ora con solo select e where: 
# con pipe inizializzate male perché quella parte la devo ancora fare
# {
# 'pipe_1': 'from.add(where_1_op).add(select_2_op)', 
#   'pipe_2': 'from.add(select_3_op)', 
#   'pipe_0': 'join.add(select_4_op)'
#}

#devo trovare il modo di formattarlo automaticamente
#'auto where_1_op = Where_Builder<sensor_q1_where_5_struct>(\n        
# [](const sensor_q1_where_5_struct& in) -> bool {\n    return (((in.humidity > 20) && (in.temperature > 20)) && (in.temperature < 30));\n}\n    )\n    
# .withName("where_sensor_q1_where_5")\n    
# .withParallelism(1)\n    
# .build();',
# 
# 'auto select_2_op = Select_Builder<sensor_q1_select_3_struct_in, sensor_q1_select_3_struct_out>(\n
#    [](const sensor_q1_select_3_struct_in& in) -> sensor_q1_select_3_struct_out {
# \n    sensor_q1_select_3_struct_out out;\n    
#       out.sensor_id = in.sensor_id;\n    
#       out.avg_temp = in.AVG_temperature;\n   
#       out.conteggio = in.COUNT_;\n    
#       return out;\n}\n    
# )\n    
# .withName("select_sensor_q1_select_3")\n    
# .withParallelism(1)\n    
# .build();', 
# 
# 'auto select_3_op = Select_Builder<sensor_q1_where_5_struct, sensor_q2_select_7_struct_out>(\n        
#    [](const sensor_q1_where_5_struct& in) -> sensor_q2_select_7_struct_out {\n
#       sensor_q2_select_7_struct_out out;\n    
#       out.sensor_id = in.sensor_id;\n    
#       out.humidity = in.humidity;\n    
#       return out;\n}\n    
# )\n    
# .withName("select_sensor_q2_select_7")\n    
# .withParallelism(1)\n    
# .build();', 
# 
# 'auto select_4_op = Select_Builder<q1_q2_join_select_1_struct_in, q1_q2_join_select_1_struct_out>(\n
#    [](const q1_q2_join_select_1_struct_in& in) -> q1_q2_join_select_1_struct_out {\n   
#       q1_q2_join_select_1_struct_out out;\n    
#       out.sensor_id = in.sensor_id;\n    
#       out.avg_temp = in.avg_temp;\n    
#       out.humidity = in.humidity;\n    
#       return out;\n}\n    
# )\n    
# .withName("select_q1_q2_join_select_1")\n    
# .withParallelism(1)\n    
# .build();'
