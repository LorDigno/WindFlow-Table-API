#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "avg_selling_price_by_seller_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t avg_selling_price_by_seller_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_winning_price_per_auction_by_seller_from_6>( "/home/user/TableAPI/data_streams/auction.csv",
    [](const std::string& line, source_winning_price_per_auction_by_seller_from_6& record, uint64_t& timestamp) {
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
    .withName("winning_price_per_auction_by_seller_from_6")
    .withHeader()
    .withParallelism(2, 512000ULL)
    .withOrderedEventTime(avg_selling_price_by_seller_epoch)
    .build();

    auto from_2_op = Table_Source_Builder<source_winning_price_per_auction_by_seller_from_7>( "/home/user/TableAPI/data_streams/bid.csv",
    [](const std::string& line, source_winning_price_per_auction_by_seller_from_7& record, uint64_t& timestamp) {
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
    .withName("winning_price_per_auction_by_seller_from_7")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(avg_selling_price_by_seller_epoch)
    .build();

    auto left_unifier_3_op = Select_Builder<source_winning_price_per_auction_by_seller_from_6, source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7>(
        [](const source_winning_price_per_auction_by_seller_from_6& in) -> source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 {
    source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 out;
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
    .withName("left_unifier_3_op")
    .withParallelism(2)
    .build();

    auto right_unifier_4_op = Select_Builder<source_winning_price_per_auction_by_seller_from_7, source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7>(
        [](const source_winning_price_per_auction_by_seller_from_7& in) -> source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 {
    source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 out;
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
    .withName("right_unifier_4_op")
    .withParallelism(2)
    .build();

    auto join_5_op = Table_Interval_Join_Builder<source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7, source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7, winning_price_per_auction_by_seller_join_interval_5_key_struct>(
    [](const source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7& left, const source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7& right) -> std::optional<source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7> {
    if( !((right.bid_dateTime <= left.expires))){
        return std::nullopt;
    }

    source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 out{};
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
    -3456000000000,
    3456000000000
)
    .withName("winning_price_per_auction_by_seller_join_interval_5")
    .withParallelism(2)
    .withKeyBy([](const source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7& in) -> winning_price_per_auction_by_seller_join_interval_5_key_struct {
    winning_price_per_auction_by_seller_join_interval_5_key_struct out;
    out.auction_id = in.auction_id;
    return out;
})
    .build_keyed();


    auto window_group_6_op = Windowed_Group_Builder<source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7, winning_price_per_auction_by_seller_window_group_by_4_struct_out, winning_price_per_auction_by_seller_window_group_by_4_key_struct>(
    [](const source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7& in, winning_price_per_auction_by_seller_window_group_by_4_struct_out& out) -> void {
    out.auction_id = in.auction_id;
    out.seller = in.seller;

    auto MAX_price_tmp = in.price; 
if( MAX_price_tmp > out.MAX_price ){
    out.MAX_price = MAX_price_tmp;
}
}
)
    .withName("winning_price_per_auction_by_seller_window_group_by_4")
    .withTBWindow(172800000000ULL, 172800000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7& in) -> winning_price_per_auction_by_seller_window_group_by_4_key_struct {
    winning_price_per_auction_by_seller_window_group_by_4_key_struct out;
    out.auction_id = in.auction_id;
    out.seller = in.seller;
    return out;
})
    .build_keyed();


    auto select_7_op = Select_Builder<winning_price_per_auction_by_seller_window_group_by_4_struct_out, winning_price_per_auction_by_seller_select_3_struct_out>(
        [](const winning_price_per_auction_by_seller_window_group_by_4_struct_out& in) -> winning_price_per_auction_by_seller_select_3_struct_out {
    winning_price_per_auction_by_seller_select_3_struct_out out;
    out.seller = in.seller;
    out.final = in.MAX_price;
    return out;
}
    )
    .withName("select_7_op")
    .withParallelism(2)
    .build();

    auto window_group_8_op = Windowed_Group_Builder<winning_price_per_auction_by_seller_select_3_struct_out, avg_selling_price_by_seller_window_group_by_2_struct_out, avg_selling_price_by_seller_window_group_by_2_key_struct>(
    [](const winning_price_per_auction_by_seller_select_3_struct_out& in, avg_selling_price_by_seller_window_group_by_2_struct_out& out) -> void {
    out.seller = in.seller;

    out.COUNT += 1;
    out.SUM_final += in.final;
    out.AVG_final = out.SUM_final / out.COUNT ;
}
)
    .withName("avg_selling_price_by_seller_window_group_by_2")
    .withCBWindow(10ULL, 1ULL)
    .withParallelism(2)
    .withKeyBy([](const winning_price_per_auction_by_seller_select_3_struct_out& in) -> avg_selling_price_by_seller_window_group_by_2_key_struct {
    avg_selling_price_by_seller_window_group_by_2_key_struct out;
    out.seller = in.seller;
    return out;
})
    .build_keyed();


    auto select_9_op = Select_Builder<avg_selling_price_by_seller_window_group_by_2_struct_out, avg_selling_price_by_seller_select_1_struct_out>(
        [](const avg_selling_price_by_seller_window_group_by_2_struct_out& in) -> avg_selling_price_by_seller_select_1_struct_out {
    avg_selling_price_by_seller_select_1_struct_out out;
    out.seller = in.seller;
    out.AVG_final = in.AVG_final;
    return out;
}
    )
    .withName("select_9_op")
    .withParallelism(2)
    .build();

    auto sink_10_op = Table_Sink_Builder<avg_selling_price_by_seller_select_1_struct_out>("avg_selling_price_by_seller",
    [](const avg_selling_price_by_seller_select_1_struct_out& record, std::ostream& os) {
 
    os << record.seller << ",";
 
    os << record.AVG_final;
}
)
    .withName("avg_selling_price_by_seller_sink_8")
    .withParallelism(2)
    .withHeader("seller,AVG_final")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "avg_selling_price_by_seller", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(left_unifier_3_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(right_unifier_4_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_5_op).add(window_group_6_op).add(select_7_op).add(window_group_8_op).add(select_9_op).add_sink(sink_10_op);

    topology.run();
    return 0;
}