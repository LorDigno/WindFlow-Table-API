from windflow_table_api import *

env = TableEnvironment()

schema = (SchemaBuilder()
                 .add_column("key", DataTypes.STRING)
                 .add_column("number", DataTypes.DOUBLE)
                 .build()
                )

tab = env.table_from_file("test.csv", schema)

tab.name_draft("group_keyed_test")
q = tab.group_by("key").select("key", avg("number"), avg("number").alias("media"))

tab.name_draft("group_global_test")
q2 = tab.select(count("key").alias("uniques"))

env.execute(q, output_dir="./output", rexecute=True)
env.execute(q2, output_dir="./output", rexecute=True)
