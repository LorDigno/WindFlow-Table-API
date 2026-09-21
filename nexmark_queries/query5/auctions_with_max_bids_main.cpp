#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "auctions_with_max_bids_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t auctions_with_max_bids_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_bids_counter_per_auction_from_5>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_bids_counter_per_auction_from_5& record, uint64_t& timestamp) {
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
    .withName("bids_counter_per_auction_from_5")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(auctions_with_max_bids_epoch)
    .build();

    auto window_group_2_op = Windowed_Group_Builder<source_bids_counter_per_auction_from_5, bids_counter_per_auction_window_group_by_4_struct_out, bids_counter_per_auction_window_group_by_4_key_struct>(
    [](const source_bids_counter_per_auction_from_5& in, bids_counter_per_auction_window_group_by_4_struct_out& out) -> void {
    out.auction_id = in.auction_id;

    out.COUNT += 1;
}
)
    .withName("bids_counter_per_auction_window_group_by_4")
    .withTBWindow(28800000000ULL, 14400000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_bids_counter_per_auction_from_5& in) -> bids_counter_per_auction_window_group_by_4_key_struct {
    bids_counter_per_auction_window_group_by_4_key_struct out;
    out.auction_id = in.auction_id;
    return out;
})
    .build_keyed();


    auto select_3_op = Select_Builder<bids_counter_per_auction_window_group_by_4_struct_out, bids_counter_per_auction_select_3_struct_out>(
        [](const bids_counter_per_auction_window_group_by_4_struct_out& in) -> bids_counter_per_auction_select_3_struct_out {
    bids_counter_per_auction_select_3_struct_out out;
    out.auction_id = in.auction_id;
    out.bids_counter = in.COUNT;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto from_4_op = Table_Source_Builder<source_bids_counter_per_auction_from_5>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_bids_counter_per_auction_from_5& record, uint64_t& timestamp) {
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
    .withName("bids_counter_per_auction_from_5")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(auctions_with_max_bids_epoch)
    .build();

    auto window_group_5_op = Windowed_Group_Builder<source_bids_counter_per_auction_from_5, bids_counter_per_auction_window_group_by_4_struct_out, bids_counter_per_auction_window_group_by_4_key_struct>(
    [](const source_bids_counter_per_auction_from_5& in, bids_counter_per_auction_window_group_by_4_struct_out& out) -> void {
    out.auction_id = in.auction_id;

    out.COUNT += 1;
}
)
    .withName("bids_counter_per_auction_window_group_by_4")
    .withTBWindow(28800000000ULL, 14400000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_bids_counter_per_auction_from_5& in) -> bids_counter_per_auction_window_group_by_4_key_struct {
    bids_counter_per_auction_window_group_by_4_key_struct out;
    out.auction_id = in.auction_id;
    return out;
})
    .build_keyed();


    auto select_6_op = Select_Builder<bids_counter_per_auction_window_group_by_4_struct_out, bids_counter_per_auction_select_3_struct_out>(
        [](const bids_counter_per_auction_window_group_by_4_struct_out& in) -> bids_counter_per_auction_select_3_struct_out {
    bids_counter_per_auction_select_3_struct_out out;
    out.auction_id = in.auction_id;
    out.bids_counter = in.COUNT;
    return out;
}
    )
    .withName("select_6_op")
    .withParallelism(2)
    .build();

    auto window_group_7_op = Windowed_Group_Builder<bids_counter_per_auction_select_3_struct_out, max_bid_count_window_group_by_7_struct_out>(
    [](const bids_counter_per_auction_select_3_struct_out& in, max_bid_count_window_group_by_7_struct_out& out) -> void {

    auto MAX_bids_counter_tmp = in.bids_counter; 
if( MAX_bids_counter_tmp > out.MAX_bids_counter ){
    out.MAX_bids_counter = MAX_bids_counter_tmp;
}
}
)
    .withName("max_bid_count_window_group_by_7")
    .withTBWindow(14400000000ULL, 14400000000ULL)
    .build();


    auto select_8_op = Select_Builder<max_bid_count_window_group_by_7_struct_out, max_bid_count_select_6_struct_out>(
        [](const max_bid_count_window_group_by_7_struct_out& in) -> max_bid_count_select_6_struct_out {
    max_bid_count_select_6_struct_out out;
    out.bids_counter = in.MAX_bids_counter;
    return out;
}
    )
    .withName("select_8_op")
    .withParallelism(2)
    .build();

    auto left_unifier_9_op = Select_Builder<bids_counter_per_auction_select_3_struct_out, bids_counter_per_auction_select_3_struct_out>(
        [](const bids_counter_per_auction_select_3_struct_out& in) -> bids_counter_per_auction_select_3_struct_out {
    bids_counter_per_auction_select_3_struct_out out;
    out.auction_id = in.auction_id;
    out.bids_counter = in.bids_counter;
    return out;
}
    )
    .withName("left_unifier_9_op")
    .withParallelism(2)
    .build();

    auto right_unifier_10_op = Select_Builder<max_bid_count_select_6_struct_out, bids_counter_per_auction_select_3_struct_out>(
        [](const max_bid_count_select_6_struct_out& in) -> bids_counter_per_auction_select_3_struct_out {
    bids_counter_per_auction_select_3_struct_out out;
    out.bids_counter = in.bids_counter;
    return out;
}
    )
    .withName("right_unifier_10_op")
    .withParallelism(2)
    .build();

    auto join_11_op = Table_Interval_Join_Builder<bids_counter_per_auction_select_3_struct_out, bids_counter_per_auction_select_3_struct_out, max_bid_count_select_6_struct_out>(
    [](const bids_counter_per_auction_select_3_struct_out& left, const bids_counter_per_auction_select_3_struct_out& right) -> std::optional<bids_counter_per_auction_select_3_struct_out> {

    bids_counter_per_auction_select_3_struct_out out{};
    out.auction_id = left.auction_id;
    out.bids_counter = left.bids_counter;
    return out;
},
    -14400000000,
    14400000000
)
    .withName("auctions_with_max_bids_join_interval_2")
    .withParallelism(2)
    .withKeyBy([](const bids_counter_per_auction_select_3_struct_out& in) -> max_bid_count_select_6_struct_out {
    max_bid_count_select_6_struct_out out;
    out.bids_counter = in.bids_counter;
    return out;
})
    .build_keyed();


    auto select_12_op = Select_Builder<bids_counter_per_auction_select_3_struct_out, bids_counter_per_auction_window_group_by_4_key_struct>(
        [](const bids_counter_per_auction_select_3_struct_out& in) -> bids_counter_per_auction_window_group_by_4_key_struct {
    bids_counter_per_auction_window_group_by_4_key_struct out;
    out.auction_id = in.auction_id;
    return out;
}
    )
    .withName("select_12_op")
    .withParallelism(2)
    .build();

    auto sink_13_op = Table_Sink_Builder<bids_counter_per_auction_window_group_by_4_key_struct>("auctions_with_max_bids",
    [](const bids_counter_per_auction_window_group_by_4_key_struct& record, std::ostream& os) {
 
    os << record.auction_id;
}
)
    .withName("auctions_with_max_bids_sink_8")
    .withParallelism(2)
    .withHeader("auction_id")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "auctions_with_max_bids", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(window_group_2_op).add(select_3_op).add(left_unifier_9_op);

    auto& pipe_2 = topology.add_source(from_4_op).add(window_group_5_op).add(select_6_op).add(window_group_7_op).add(select_8_op).add(right_unifier_10_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_11_op).add(select_12_op).add_sink(sink_13_op);

    topology.run();
    return 0;
}