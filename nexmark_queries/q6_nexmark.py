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

#---    QUERY 6
#--- What is the average selling price per seller for their last 10 closed auctions.
#--- Non viene bene

valid_bid = (col("bid_dateTime") <= col("expires"))

#nel dataset attuale una auction dura 7/8 ore
time_window = Window.createTBWindow(
    Duration.days(2)
)

#interval brutto per simulare la join completa sul mese
interval = Interval(
    Duration.days(-40),
    Duration.days(+40)
)

auction_winners = (auction
    .name_query("winning_price_per_auction_by_seller")
    .join(bid, ["auction_id"], attachment= interval, where= valid_bid)
    .group_by("auction_id", "seller", window= time_window)
    .select("seller", max("price").alias("final"))
)

count_window = Window.createCBWindow(10, 1)

q6 = (auction_winners
    .name_query("avg_selling_price_by_seller")
    .group_by("seller", window= count_window)
    .select("seller", avg("final"))
)

env.execute(q6, rexecute= True, output_dir= "./query6")
