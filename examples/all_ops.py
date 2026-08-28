from windflow_table_api import *

#query di prova per testare tutti gli operatori possibili via builders.py

env = TableEnvironment(par= 2, policy= TimePolicy.EVENT_TIME)

sensors = (SchemaBuilder()
    .add_column("sensor_id", DataTypes.STRING)
    .add_column("temperature", DataTypes.DOUBLE)
    .add_column("humidity", DataTypes.DOUBLE)
    .build()
)

source = env.table_from_file(
    file_path= "sensor_stream_input.csv", 
    schema= sensors, 
    name= "sensor_source",
    time_col= TimeCol("timestamp", TimeTypes.MICROSECONDS)
)

hot = col("temperature") > 30
wet = col("humidity") > 50

source.name_draft("hot")
q1 = source.where(hot).select("sensor_id", "temperature")

source.name_draft("wet")
q2 = source.where(wet).select("sensor_id", "humidity")

interval = Interval(
    lower_bound= Duration(-5, TimeTypes.DAYS),
    upper_bound= Duration(+5, TimeTypes.DAYS)
)

q1.name_draft("hot_joined_wet")
q3 = q1.join("sensor_id", other= q2, attachment= interval).select("sensor_id", "temperature", "humidity")

q3.name_draft("gotta_put_a_union_in_there")
q4 = q3.union(source).select("sensor_id", "temperature", "humidity")

q4.name_draft("gotta_put_an_intersect_in_there")
q5 = q4.intersect(source).select("sensor_id", "temperature", "humidity")

win = Window.createTBWindow(
    size= Duration(10, TimeTypes.DAYS),
    slide= Duration(5, TimeTypes.DAYS)
)

q5.name_draft("avg_temp_and_hum")
q6 = q5.group_by("sensor_id", window= win).select(
                            "sensor_id", 
                            avg("temperature").alias("avg_temp"),
                            avg("humidity").alias("avg_hum")
                            )

env.execute(q6, "./output", True)
