from windflow_table_api import *
from pathlib import Path

gen = SchemaGenerator()
par = JsonParser(Path("./output"))

gra = par.parse_query("q1_q2_join")

def post_visit(root: OpNode):
    for p in root.parents:
        post_visit(p)  

    if root.schema_in:
        gen.get_or_create_struct(root.schema_in, "q1_q2_join_input")

    if root.schema_out:  
        gen.get_or_create_struct(root.schema_out, "q1_q2_join_output")    

post_visit(gra.target_root)
       
path = gen.write_header_file(Path("./output"), query_id="q1_q2_join")
print(f"Header generato in: {path}") 