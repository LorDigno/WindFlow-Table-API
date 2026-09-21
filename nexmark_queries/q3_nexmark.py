from windflow_table_api import *
from pathlib import Path

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME,
    epoch= ("epoch da decidere una volta preso il dataset", TimeFormats.ISO8601)
)

from windflow_table_api import *
from pathlib import Path

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME,
    epoch=("2026-09-01T00:00:00.000Z", TimeFormats.ISO8601)
)

#---- auction
auction_schema = (SchemaBuilder()
    .add_column("auction_id", DataTypes.BIGINT)
    .add_column("item_name", DataTypes.STRING)
    .add_column("description", DataTypes.STRING)
    .add_column("initial_bid", DataTypes.BIGINT)
    .add_column("reserve", DataTypes.BIGINT)
    .add_column("auction_dateTime", TimeFormats.ISO8601)    #timestamp
    .add_column("expires", TimeFormats.ISO8601)
    .add_column("seller", DataTypes.BIGINT)                 #id di un Person
    .add_column("category", DataTypes.BIGINT)
    .build()
)

auction_config = InputFileConfiguration(
    path = Path("../data_streams/auction.csv"),
    format= FileFormat.CSV,
    schema= auction_schema,
    has_header= True,
    time_col= "auction_dateTime",
    order= True,                        
    split_size= SplitSize.kilobytes(500)
)

auction = env.table_from_file(auction_config, "auction_source")

#---- person
person_schema = (SchemaBuilder()
    .add_column("person_id", DataTypes.BIGINT)              # ID univoco dell'utente
    .add_column("name", DataTypes.STRING)
    .add_column("email_address", DataTypes.STRING)
    .add_column("credit_card", DataTypes.STRING)
    .add_column("city", DataTypes.STRING)
    .add_column("state", DataTypes.STRING)
    .add_column("person_dateTime", TimeFormats.ISO8601)     # Timestamp di registrazione
    .add_column("extra", DataTypes.STRING)                   # Campo di padding standard NEXMark
    .build()
)

person_config = InputFileConfiguration(
    path = Path("../data_streams/person.csv"),
    format = FileFormat.CSV,
    schema = person_schema,
    has_header = True,
    time_col = "person_dateTime",
    order = True,                                           # da vedere
    split_size= SplitSize.kilobytes(400)
)

person = env.table_from_file(person_config, "person_source")

#---- bid
bid_schema = (SchemaBuilder()
    .add_column("auction_id", DataTypes.BIGINT)             # Riferimento ad Auction
    .add_column("bidder", DataTypes.BIGINT)                 # ID utente (Person) che fa l'offerta
    .add_column("price", DataTypes.BIGINT)                  # Valore offerta (in centesimi, coerente con initial_bid/reserve)
    .add_column("channel", DataTypes.STRING)                # Canale di provenienza offerta
    .add_column("url", DataTypes.STRING)
    .add_column("bid_dateTime", TimeFormats.ISO8601)        # Timestamp dell'offerta
    .add_column("extra", DataTypes.STRING)                   # Campo di padding standard NEXMark
    .build()
)

bid_config = InputFileConfiguration(
    path = Path("../data_streams/bid.csv"),
    format = FileFormat.CSV,
    schema = bid_schema,
    has_header = True,
    time_col = "bid_dateTime",
    order = True,                                           # da vedere
    split_size= SplitSize.megabytes(5)
)

bid = env.table_from_file(bid_config, "bid_source")

#---    QUERY 3
#--- Who is selling in OR, ID or CA in category 10, and for what auction ids?

p_cond = (
    (col("state") == "OR") | (col("state") == "CA") | (col("state") == "ID")
) 

a_cond = col("category") == 10

#altrimenti si può evitare la ridenominazione e fare con una theta-join col("seller") == col("person_id")
renamed_auction = auction.where(a_cond).rename_columns(
    {"seller": "person_id"}
)

#interval brutto per simulare la join completa
interval = Interval(
    Duration.days(-365),
    Duration.days(365)
)

q3 = (person
    .name_query("selling_in_states")
    .where(p_cond)
    #prima occasine in cui il non avere la join completa ci frega (interval placeholder)
    .join(renamed_auction, "person_id", attachment= interval)
    .select("name", "city", "state", "auction_id")        
)

env.execute(q3, rexecute=True, output_dir="./query3")
