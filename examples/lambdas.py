from windflow_table_api import *

schema1 = "SensorInput"
schema2 = "SelectedSensor"

mappings = [
    ("sensor_id", "in.sensor_id"),
    ("humidity", "in.humidity")
]

print(LambdaGenerator.map_lambda(schema1, schema2, mappings, "in"))

condition = "in.humidity >= 50.0"

print(LambdaGenerator.where_lambda(schema1, condition, "in"))
