from windflow_table_api import *

schema1 = "SensorInput"
schema2 = "SelectedSensor"
schema3 = "GroupedSensor"
schema4 = "JoinedSensors"

mappings = [
    ("sensor_id", "in.sensor_id"),
    ("humidity", "in.humidity")
]

print(LambdaGenerator.map_lambda(schema1, schema2, mappings, "in"))

condition = "in.humidity >= 50.0"

print(LambdaGenerator.where_lambda(schema1, condition, "in"))

accumulations = [
    "out.count += 1",
    "out_sum += in.temperature",
    "out.avg = out.sum / out.count"
]

print(LambdaGenerator.groupBy_lambda(schema1, schema3, mappings, accumulations, "in", "out"))

joins = [
    ("sensor_id", "grouped.sensor_id"),
    ("avg", "grouped.avg"),
    ("humidity", "selected.humidity")
]

print(LambdaGenerator.join_lambda(schema2, schema3, joins, "selected", "grouped"))
