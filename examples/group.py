from windflow_table_api import *

env = TableEnvironment()

schema = (SchemaBuilder()
                 .add_column("key", DataTypes.STRING)
                 .add_column("number", DataTypes.DOUBLE)
                 .build()
                )

tab = env.table_from_file("test.csv", schema)

tab.name_draft("group_tests")
q = tab.group_by("key").select("key", avg("number"), avg("number").alias("media"))

env.execute(q, output_dir="./output", rexecute=True)
