#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "auction_expanded_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t auction_expanded_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_auction_expanded_from_4>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/auction.csv",
    [](const std::string& line, source_auction_expanded_from_4& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    std::getline(ss, token, ',');
    record.auction_id = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.item_name = parse_STRING(token);

    std::getline(ss, token, ',');
    record.description = parse_STRING(token);

    std::getline(ss, token, ',');
    record.initial_bid = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.reserve = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.auction_dateTime = parse_ISO8601(token);
    timestamp = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.expires = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.seller = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.category = parse_BIGINT(token);

}
)
    .withName("auction_expanded_from_4")
    .withHeader()
    .withParallelism(2, 512000ULL)
    .withOrderedEventTime(auction_expanded_epoch)
    .build();

    auto where_2_op = Where_Builder<source_auction_expanded_from_4>(
        [](const source_auction_expanded_from_4& in) -> bool {
    return (in.category == 11);
}
    )
    .withName("auction_expanded_where_3")
    .withParallelism(2)
    .build();

    auto from_3_op = Table_Source_Builder<source_auction_expanded_from_5>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_auction_expanded_from_5& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    std::getline(ss, token, ',');
    record.auction_id = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.bidder = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.price = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.channel = parse_STRING(token);

    std::getline(ss, token, ',');
    record.url = parse_STRING(token);

    std::getline(ss, token, ',');
    record.bid_dateTime = parse_ISO8601(token);
    timestamp = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.extra = parse_STRING(token);

}
)
    .withName("auction_expanded_from_5")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(auction_expanded_epoch)
    .build();

    auto left_unifier_4_op = Select_Builder<source_auction_expanded_from_4, source_auction_expanded_from_4_unified_source_auction_expanded_from_5>(
        [](const source_auction_expanded_from_4& in) -> source_auction_expanded_from_4_unified_source_auction_expanded_from_5 {
    source_auction_expanded_from_4_unified_source_auction_expanded_from_5 out;
    out.auction_id = in.auction_id;
    out.item_name = in.item_name;
    out.description = in.description;
    out.initial_bid = in.initial_bid;
    out.reserve = in.reserve;
    out.auction_dateTime = in.auction_dateTime;
    out.expires = in.expires;
    out.seller = in.seller;
    out.category = in.category;
    return out;
}
    )
    .withName("left_unifier_4_op")
    .withParallelism(2)
    .build();

    auto right_unifier_5_op = Select_Builder<source_auction_expanded_from_5, source_auction_expanded_from_4_unified_source_auction_expanded_from_5>(
        [](const source_auction_expanded_from_5& in) -> source_auction_expanded_from_4_unified_source_auction_expanded_from_5 {
    source_auction_expanded_from_4_unified_source_auction_expanded_from_5 out;
    out.auction_id = in.auction_id;
    out.bidder = in.bidder;
    out.price = in.price;
    out.channel = in.channel;
    out.url = in.url;
    out.bid_dateTime = in.bid_dateTime;
    out.extra = in.extra;
    return out;
}
    )
    .withName("right_unifier_5_op")
    .withParallelism(2)
    .build();

    auto join_6_op = Table_Interval_Join_Builder<source_auction_expanded_from_4_unified_source_auction_expanded_from_5, source_auction_expanded_from_4_unified_source_auction_expanded_from_5, auction_expanded_join_interval_2_key_struct>(
    [](const source_auction_expanded_from_4_unified_source_auction_expanded_from_5& left, const source_auction_expanded_from_4_unified_source_auction_expanded_from_5& right) -> std::optional<source_auction_expanded_from_4_unified_source_auction_expanded_from_5> {

    source_auction_expanded_from_4_unified_source_auction_expanded_from_5 out{};
    out.auction_id = left.auction_id;
    out.item_name = left.item_name;
    out.description = left.description;
    out.initial_bid = left.initial_bid;
    out.reserve = left.reserve;
    out.auction_dateTime = left.auction_dateTime;
    out.expires = left.expires;
    out.seller = left.seller;
    out.category = left.category;
    out.bidder = right.bidder;
    out.price = right.price;
    out.channel = right.channel;
    out.url = right.url;
    out.bid_dateTime = right.bid_dateTime;
    out.extra = right.extra;
    return out;
},
    -60000000,
    43200000000
)
    .withName("auction_expanded_join_interval_2")
    .withParallelism(2)
    .withKeyBy([](const source_auction_expanded_from_4_unified_source_auction_expanded_from_5& in) -> auction_expanded_join_interval_2_key_struct {
    auction_expanded_join_interval_2_key_struct out;
    out.auction_id = in.auction_id;
    return out;
})
    .build_keyed();


    auto sink_7_op = Table_Sink_Builder<source_auction_expanded_from_4_unified_source_auction_expanded_from_5>("auction_expanded",
    [](const source_auction_expanded_from_4_unified_source_auction_expanded_from_5& record, std::ostream& os) {
 
    os << record.auction_id << ",";
 
    os << record.item_name << ",";
 
    os << record.description << ",";
 
    os << record.initial_bid << ",";
 
    os << record.reserve << ",";
 
    os << reformat_ISO8601(record.auction_dateTime) << ",";
 
    os << reformat_ISO8601(record.expires) << ",";
 
    os << record.seller << ",";
 
    os << record.category << ",";
 
    os << record.bidder << ",";
 
    os << record.price << ",";
 
    os << record.channel << ",";
 
    os << record.url << ",";
 
    os << reformat_ISO8601(record.bid_dateTime) << ",";
 
    os << record.extra;
}
)
    .withName("auction_expanded_sink_6")
    .withParallelism(2)
    .withHeader("auction_id,item_name,description,initial_bid,reserve,auction_dateTime,expires,seller,category,bidder,price,channel,url,bid_dateTime,extra")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "auction_expanded", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(where_2_op).add(left_unifier_4_op);

    auto& pipe_2 = topology.add_source(from_3_op).add(right_unifier_5_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_6_op).add_sink(sink_7_op);

    topology.run();
    return 0;
}