from windflow_table_api import *

env = TableEnvironment(policy=TimePolicy.EVENT_TIME)

sensor_schema = (SchemaBuilder()
                 .add_column("sensor_id", DataTypes.STRING)
                 .add_column("temperature", DataTypes.DOUBLE)
                 .add_column("humidity", DataTypes.DOUBLE)
                 .build()
                )

tab = env.table_from_file("sensor_stream_input.csv", 
                          sensor_schema, 
                          "sensor_source",
                          TimeCol("timestamp", TimeTypes.MILLISECONDS)
                          )

cond = (
    (col("humidity") > 20) & (col("temperature") > 20) & (col("temperature") < 30)
)

window = Window.createTBWindow(
    Duration(10, TimeTypes.MINUTES),
    Duration(5, TimeTypes.MINUTES)
)

interval = Interval(
    Duration(-5, TimeTypes.MINUTES),
    Duration(5, TimeTypes.MINUTES)
)

tab.name_draft("sensor_q1")
q1 = (tab
     .where(cond)
     .group_by("sensor_id", window=window)
     .select("sensor_id", avg("temperature").alias("avg_temp"), count().alias("conteggio"))
    )   

tab.name_draft("sensor_q2")
q2 = (tab.select("sensor_id", "humidity", distinct=True))

q1.name_draft("q1_q2_join")
q3 = (q1                                    
      .join("sensor_id", other= q2, attachment=interval)                            
      .select("sensor_id", "avg_temp", "humidity")      
      )

env.execute(q3, "./output", rexecute=True)
