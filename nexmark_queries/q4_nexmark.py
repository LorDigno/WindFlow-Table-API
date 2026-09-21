from windflow_table_api import *
from pathlib import Path

env = TableEnvironment(
    par= 2, 
    policy=TimePolicy.EVENT_TIME,
    epoch= ("epoch da decidere una volta preso il dataset", TimeFormats.ISO8601)
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
    path = Path("attualmente non c'è"),
    format= FileFormat.CSV,
    schema= auction_schema,
    has_header= True,
    time_col= "auction_dateTime",
    order= True,                        #da vedere
    delay= None,                        #da vedere
    #eventuale splitsize in base a quanto sarà grande il file
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
    .build()
)

person_config = InputFileConfiguration(
    path = Path("attualmente non c'è"),
    format = FileFormat.CSV,
    schema = person_schema,
    has_header = True,
    time_col = "person_dateTime",
    order = True,                                           # da vedere
    delay = None,                                           # da vedere
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
    .build()
)

bid_config = InputFileConfiguration(
    path = Path("attualmente non c'è"),
    format = FileFormat.CSV,
    schema = bid_schema,
    has_header = True,
    time_col = "bid_dateTime",
    order = True,                                           # da vedere
    delay = None,                                           # da vedere
)

bid = env.table_from_file(bid_config, "bid_source")

#---    QUERY 4
#--- Select the average of the wining bid prices for all auctions in each category.
#--- Non viene bene

#interval brutto per simulare la join completa
interval = Interval(
    Duration.days(-365),
    Duration.days(365)
)

valid_bid = (col("bid_dateTime") <= col("expires"))

#necessario per rilasciare un singolo massimo per auction
#il problema è che così richiediamo che le auction siano incluse in slot da 30 giorni
window = Window.createTBWindow(
    Duration.days(30)
)

q4 = (auction
    .join(bid, "auction_id", attachment= interval, where= valid_bid)
    .group_by("auction_id", "category", window= window)
    .select("category", max("price").alias("final"))
    #creazione di un oggetto query nascosto
    .group_by("category")
    .select("category", avg("final").alias("avg_price"))
)
