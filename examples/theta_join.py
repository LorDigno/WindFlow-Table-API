from pathlib import Path
import sys
from windflow_table_api import *

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME,
    epoch= ("2026-09-01T06:00:00.000Z", TimeFormats.ISO8601)
)

sensor_schema = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temperature", DataTypes.DOUBLE)
                 .add_column("humidity", DataTypes.DOUBLE)
                 .build()
                )

source_config = InputFileConfiguration(
    path = Path("../data_streams/sensor_real_stream.csv"),
    format= FileFormat.CSV,
    schema= sensor_schema,
    split_size= SplitSize.kilobytes(1),
    has_header= True,
    time_col= TimeCol("timestamp", TimeFormats.ISO8601),
    order= False,
    delay= Duration.hours(2)
)

tab = env.table_from_file(source_config, "sensor_stream_input")

renamed_self = tab.name_query("renaming_for_self_join").rename_columns(
    {
        "sensor_id": "sens",
        "temperature": "temp",
        "humidity": "hum"
    }
)

interval = Interval(
    Duration.minutes(-30),
    Duration.minutes(30)
)

theta = (col("hum") > 50) & (col("temperature") < 20)

q1 = (tab
      .name_query("self_theta_join")
      .join(renamed_self, attachment=interval, where= theta)
      .select("sensor_id", "sens", "temperature", "hum")
)

env.execute(q1, rexecute=True, output_dir="./self_theta_join_output")
