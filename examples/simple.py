from pathlib import Path
from windflow_table_api import *

env = TableEnvironment(policy=TimePolicy.INGRESS_TIME)

sensor_schema = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temperature", DataTypes.DOUBLE)
                 .add_column("humidity", DataTypes.DOUBLE)
                 .build()
                )

tab = env.table_from_file("sensor_stream_input.csv",
                          sensor_schema, 
                          "sensor_source"       #id associato alla query
                          )

#definisco la condizione per il where
cond = (col("temperature") < 10) & (col("humidity") < 20)

tab.name_draft("cold_and_dry")      #definisce l'id della query risultante
q1 = (tab
      .where(cond)
      .select("sensor_id", "temperature", "humidity")
)

time_win = Window.createTBWindow(
    Duration.minutes(2),        #size
    Duration.minutes(1)         #slide
)

q1.name_draft("avg_cold_temperature")
q2 = (q1
      .group_by("sensor_id", window = time_win)
      .select("sensor_id", avg("temperature").alias("avg_temp"))
)

#crea i file JSON delle due query
env.execute(q2, output_dir="./output", rexecute=True)

#esempi di traduzione del codice
gen = SchemaGenerator()

#schema nel json
sensor_json = {
                "sensor_id": "STRING",
                "temperature": "DOUBLE",
                "humidity": "DOUBLE"
}

gen.get_or_create_struct(sensor_json, "sensor_input", needs_hash=True)
gen.write_header_file(Path("./output"), "cold_and_dry",)


