from windflow_table_api import *
from pathlib import Path

gen = SchemaGenerator()

s1 = {"sensor_id": "STRING", "temperature": "DOUBLE"}
struct1 = gen.get_or_create_struct(s1, name_hint="SensorData")

# Schema con campi invertiti (equivalente) -> Deduplicato!
s2 = {"temperature": "DOUBLE", "sensor_id": "STRING"}
struct2 = gen.get_or_create_struct(s2, name_hint="OtherData", needs_hash=True)

# Genera il file header C++
path = gen.write_header_file(Path("./output"), query_id="q1")
print(f"Header generato in: {path}")
