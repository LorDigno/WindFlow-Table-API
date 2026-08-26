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
        gen.get_or_create_struct(root.schema_out, "q1_q2_join_output", True, True)    

post_visit(gra.target_root)
       
path = gen.write_header_file(Path("./output"), query_id="q1_q2_join")
print(f"Header generato in: {path}")

#prova con finestre e valori di default 
gen2 = SchemaGenerator()

schema_in = {
    "sensor_id": "STRING",
    "temperature": "DOUBLE",
    "humidity": "DOUBLE"
}

key_schema = {
    "sensor_id": "STRING"
}

schema_out = {
    "sensor_id": "STRING",
    "SUM_temperature": "DOUBLE",
    "MAX_humidity": "DOUBLE"
}

defaults = {
    "SUM_temperature": "0.0",
    "MAX_humidity": "std::numeric_limits<double>::lowest()"
}

gen2.get_or_create_struct(schema_in, "Sensor_Input")
tmp = gen2.get_or_create_struct(key_schema, "Sensor_Key", needs_hash=True)
gen2.get_or_create_struct(
    schema_out, 
    "Grouped_Sensors", 
    needs_win=True, 
    key_struct=tmp,
    defaults=defaults
)

path = gen2.write_header_file(Path("./output"), query_id="group_test")
print(f"Header generato in: {path}")