from pathlib import Path
from windflow_table_api import *

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME,
    epoch= ("2026-09-04T08:00:00.000Z", TimeFormats.ISO8601)
)

sensor_schema = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temperature", DataTypes.DOUBLE)
                 .add_column("humidity", DataTypes.DOUBLE)
                 .build()
                )

source_config = InputFileConfiguration(
    path = Path("../data_streams/sensor_input_stream.csv"),
    format= FileFormat.CSV,
    schema= sensor_schema, 
    has_header= True,
    time_col= TimeCol("timestamp", TimeFormats.ISO8601),
    order= True,
)

tab = env.table_from_file(source_config, "sensor_stream_input")

tab.name_draft("sum_of_binary")
q1 = (tab
    .group_by("sensor_id")
    .select(
        "sensor_id",
        sum(col("temperature") + col("humidity"))
    )
)
env.execute(q1, output_dir="./aggregates", rexecute=True)
