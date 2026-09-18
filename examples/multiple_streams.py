from pathlib import Path
from windflow_table_api import *

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME, 
    epoch= ("2026-09-04T08:00:00.000Z", TimeFormats.ISO8601)
)

sensor_schema1 = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temperature", DataTypes.DOUBLE)
                 .add_column("humidity", DataTypes.DOUBLE)
                 .build()
                )

sensor_schema2 = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temp", DataTypes.DOUBLE)
                 .add_column("hum", DataTypes.DOUBLE)
                 .build()
                )

source_config_ordered = InputFileConfiguration(
    path = Path("../data_streams/sensor_input_stream.csv"),
    format= FileFormat.CSV,
    schema= sensor_schema1, 
    has_header= True,
    time_col= TimeCol("timestamp", TimeFormats.ISO8601),
    order= True,
)

src_ord = env.table_from_file(source_config_ordered, "sensor_ordered")

source_config_real = InputFileConfiguration(
    path = Path("../data_streams/sensor_second_stream.csv"),
    format= FileFormat.CSV,
    schema= sensor_schema2, 
    has_header= True,
    time_col= TimeCol("timestamp", TimeFormats.ISO8601),
    order= False,
    delay= Duration.minutes(3)
)

src_real = env.table_from_file(source_config_real, "sensor_real")

window = Window.createTBWindow(
    Duration.minutes(4),
    Duration.minutes(2)
)

q1 = (src_real
    .name_query("multiple_join")
    .join(src_ord, "sensor_id", attachment= window)
    .select("sensor_id", "temp", "temperature", "hum", "humidity")
)

env.execute(q1, rexecute=True, output_dir="./multiple")
