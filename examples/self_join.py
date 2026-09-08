from pathlib import Path
import sys
from windflow_table_api import *

env = TableEnvironment(par= 2, policy=TimePolicy.EVENT_TIME)

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

tab.name_draft("renaming_for_selfjoin")
renamed_self = tab.rename_columns(
    {
        "temperature": "temp",
        "humidity": "hum"
    }
)

interval = Interval(
    Duration.minutes(-30),
    Duration.minutes(30)
)

tab.name_draft("self_interval_join")
q1 = (tab
      .join(renamed_self, "sensor_id", attachment=interval)
      .select("sensor_id", "temperature", "hum")
)

env.execute(q1, rexecute=True, output_dir="./self_interval_join_output")
