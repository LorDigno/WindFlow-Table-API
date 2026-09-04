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
    path = "sensor_input_stream.csv",
    format= FileFormat.CSV,
    schema= sensor_schema,
    has_header= True,
    time_col= TimeCol("timestamp", TimeFormats.ISO8601),
    order= True
)

tab = env.table_from_file(source_config, "sensor_stream_input.csv")

#definisco la condizione per il where
cond = (col("temperature") < 10) & (col("humidity") < 20)

tab.name_draft("cold_and_dry")      #definisce l'id della query risultante
q1 = (tab
      .where(cond)
      .distinct()
      .select("sensor_id", "temperature", "humidity")
)

q1.name_draft("avg_cold_temperature")
q2 = (q1
      .group_by("sensor_id")
      .select("sensor_id" ,avg("temperature").alias("avg_temp"))
)

#crea i file JSON delle due query
env.execute(q2, output_dir="./output", rexecute=True)

#la parte che segue verrà poi chiamata automaticamente da execute
#è ancora in TODO quella parte

sys.argv = ["code_generator.py", 
            "avg_cold_temperature", 
            "--json-dir", "./output", 
            "--parallelism", str(env.par),
            "--time-policy", env.policy.name
]
codegen.code_generator.main()
