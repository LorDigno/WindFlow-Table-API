#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "max_bids_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t max_bids_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_max_bids_from_3>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_max_bids_from_3& record, uint64_t& timestamp) {
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
    .withName("max_bids_from_3")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(max_bids_epoch)
    .build();

    auto from_2_op = Table_Source_Builder<source_max_bids_from_3>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_max_bids_from_3& record, uint64_t& timestamp) {
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
    .withName("window_max_from_6")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(max_bids_epoch)
    .build();

    auto window_group_3_op = Windowed_Group_Builder<source_max_bids_from_3, window_max_window_group_by_5_struct_out>(
    [](const source_max_bids_from_3& in, window_max_window_group_by_5_struct_out& out) -> void {

    auto MAX_price_tmp = in.price; 
if( MAX_price_tmp > out.MAX_price ){
    out.MAX_price = MAX_price_tmp;
}
}
)
    .withName("window_max_window_group_by_5")
    .withTBWindow(3600000000ULL, 3600000000ULL)
    .build();


    auto select_4_op = Select_Builder<window_max_window_group_by_5_struct_out, window_max_select_4_struct_out>(
        [](const window_max_window_group_by_5_struct_out& in) -> window_max_select_4_struct_out {
    window_max_select_4_struct_out out;
    out.current_max = in.MAX_price;
    return out;
}
    )
    .withName("select_4_op")
    .withParallelism(2)
    .build();

    auto left_unifier_5_op = Select_Builder<source_max_bids_from_3, source_max_bids_from_3_unified_window_max_select_4_struct_out>(
        [](const source_max_bids_from_3& in) -> source_max_bids_from_3_unified_window_max_select_4_struct_out {
    source_max_bids_from_3_unified_window_max_select_4_struct_out out;
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
    .withName("left_unifier_5_op")
    .withParallelism(2)
    .build();

    auto right_unifier_6_op = Select_Builder<window_max_select_4_struct_out, source_max_bids_from_3_unified_window_max_select_4_struct_out>(
        [](const window_max_select_4_struct_out& in) -> source_max_bids_from_3_unified_window_max_select_4_struct_out {
    source_max_bids_from_3_unified_window_max_select_4_struct_out out;
    out.current_max = in.current_max;
    return out;
}
    )
    .withName("right_unifier_6_op")
    .withParallelism(2)
    .build();

    auto join_7_op = Table_Interval_Join_Builder<source_max_bids_from_3_unified_window_max_select_4_struct_out, source_max_bids_from_3_unified_window_max_select_4_struct_out>(
    [](const source_max_bids_from_3_unified_window_max_select_4_struct_out& left, const source_max_bids_from_3_unified_window_max_select_4_struct_out& right) -> std::optional<source_max_bids_from_3_unified_window_max_select_4_struct_out> {
    if( !((right.current_max == left.price))){
        return std::nullopt;
    }

    source_max_bids_from_3_unified_window_max_select_4_struct_out out{};
    out.auction_id = left.auction_id;
    out.bidder = left.bidder;
    out.price = left.price;
    out.channel = left.channel;
    out.url = left.url;
    out.bid_dateTime = left.bid_dateTime;
    out.extra = left.extra;
    out.current_max = right.current_max;
    return out;
},
    0,
    3600000000
)
    .withName("max_bids_join_interval_2")
    .build();


    auto select_8_op = Select_Builder<source_max_bids_from_3_unified_window_max_select_4_struct_out, max_bids_select_1_struct_out>(
        [](const source_max_bids_from_3_unified_window_max_select_4_struct_out& in) -> max_bids_select_1_struct_out {
    max_bids_select_1_struct_out out;
    out.auction_id = in.auction_id;
    out.price = in.price;
    out.bidder = in.bidder;
    return out;
}
    )
    .withName("select_8_op")
    .withParallelism(2)
    .build();

    auto sink_9_op = Table_Sink_Builder<max_bids_select_1_struct_out>("max_bids",
    [](const max_bids_select_1_struct_out& record, std::ostream& os) {
 
    os << record.auction_id << ",";
 
    os << record.price << ",";
 
    os << record.bidder;
}
)
    .withName("max_bids_sink_7")
    .withParallelism(2)
    .withHeader("auction_id,price,bidder")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "max_bids", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(left_unifier_5_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(window_group_3_op).add(select_4_op).add(right_unifier_6_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_7_op).add(select_8_op).add_sink(sink_9_op);

    topology.run();
    return 0;
}