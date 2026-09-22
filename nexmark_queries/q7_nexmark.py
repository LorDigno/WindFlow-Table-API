from windflow_table_api import *
from pathlib import Path

env = TableEnvironment(
    include_dir= Path("../include"),
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

#---    QUERY 7
#--- Select the bids with the highest bid price in the last period.

hour_window = Window.createTBWindow(Duration.hours(1))

current_max = (bid
    .name_query("window_max")
    .group_by(window= hour_window)  #par = 1 se unkeyed
    .select(max("price").alias("current_max"))
)

interval = Interval(
    Duration.hours(0),
    Duration.hours(1)
)

theta = col("current_max") == col("price")

q7 = (bid
    .name_query("max_bids")
    #si usa un intervallo per prendere solo la finestra corrente
    .join(current_max, on = [] ,attachment= interval, where= theta)
    .select("auction_id", "price", "bidder")
)

env.execute(q7, rexecute= True, output_dir= "./query7")
