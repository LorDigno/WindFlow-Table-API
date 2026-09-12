from pathlib import Path
from windflow_table_api import *

env = TableEnvironment(par= 2, policy=TimePolicy.EVENT_TIME)

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

src = env.table_from_file(source_config, "sensor_source")

hot_cond = col("temperature") > 30

#operatori unari semplici con raggruppamento globale
src.name_draft("unary_simple_test")
q1 = (src
    .where(hot_cond)
    .distinct()
    .group_by("sensor_id")
    .select("sensor_id", count().alias("conteggio"))
)
env.execute(q1, rexecute=True, output_dir="./simple_test")

window_time = Window.createTBWindow(
    Duration.minutes(10),
    Duration.minutes(5)
)

window_count = Window.createCBWindow(10, 10)

#ridenominazione per selfjoin
src.name_draft("renamed_src")
renamed_src = src.rename_columns(
    {
        "temperature": "temp",
        "humidity": "hum"
    }
)

#raggruppamento e join su finestra
src.name_draft("window_tests")
q2 = (src
    .join(renamed_src, "sensor_id", attachment=window_time)
    .group_by("sensor_id", window= window_time)
    .select("sensor_id", avg("temperature").alias("media"))
)
env.execute(q2, rexecute=True, output_dir="./window_tests")

warm_cond = col("temperature") > 25
cold_cond = col("temperature") < 15

#query di supporto pe i test insiemistici
q3 = (src
    .where(hot_cond)
    .select("sensor_id", "temperature")    
)
q4 = (src
    .where(warm_cond)
    .select("sensor_id", "temperature")
)
q5 = (src
    .where(cold_cond)
    .select("sensor_id", "temperature")
)

#test insiemistici
q3.name_draft("union_tests")
q6 = (q3
    .union(q4)
    .union_all(q5)
    .select("sensor_id", "temperature")
    #ci devono essere tutte le cold e una sola copia di tutte quelle da warm in su
)
env.execute(q6, rexecute=True, output_dir="./union_tests")

q3.name_draft("intersect_tests")
q7 = (q3
    .intersect(q4)      
    .select("sensor_id", "temperature")
)
env.execute(q7, rexecute=True, output_dir="./intersect_tests")

interval = Interval(
    Duration.minutes(-5),
    Duration.minutes(5)
)

#ridenominazione per selfjoin senza chiave
src.name_draft("rerenamed_src")
rerenamed_src = src.rename_columns(
    {
        "sensor_id": "sens",
        "temperature": "temp",
        "humidity": "hum"
    }
)

#prove su operatori keyed senza chiavi
src.name_draft("keyless_interval_join")
q8 = (src
    .join(rerenamed_src, attachment=interval)
    .select("sensor_id", "hum", "temperature")
)
env.execute(q8, rexecute=True, output_dir="./keyless_join")

src.name_draft("keyless_window_group")
q9 = (src
    .group_by(window=window_time)
    .select(count().alias("conteggio"))
)
env.execute(q9, rexecute=True, output_dir="./keyless_group")
