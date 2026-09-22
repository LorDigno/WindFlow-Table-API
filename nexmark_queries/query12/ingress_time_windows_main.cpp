#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "ingress_time_windows_structs.hpp"

int main(int argc, char* argv[]) {

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_ingress_time_windows_from_3>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_ingress_time_windows_from_3& record, uint64_t& timestamp) {
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

    std::getline(ss, token, ',');
    record.extra = parse_STRING(token);

}
)
    .withName("ingress_time_windows_from_3")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .build();

    auto window_group_2_op = Windowed_Group_Builder<source_ingress_time_windows_from_3, ingress_time_windows_window_group_by_2_struct_out, ingress_time_windows_window_group_by_2_key_struct>(
    [](const source_ingress_time_windows_from_3& in, ingress_time_windows_window_group_by_2_struct_out& out) -> void {
    out.bidder = in.bidder;

    out.COUNT += 1;
}
)
    .withName("ingress_time_windows_window_group_by_2")
    .withTBWindow(100000ULL, 100000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_ingress_time_windows_from_3& in) -> ingress_time_windows_window_group_by_2_key_struct {
    ingress_time_windows_window_group_by_2_key_struct out;
    out.bidder = in.bidder;
    return out;
})
    .build_keyed();


    auto select_3_op = Select_Builder<ingress_time_windows_window_group_by_2_struct_out, ingress_time_windows_select_1_struct_out>(
        [](const ingress_time_windows_window_group_by_2_struct_out& in) -> ingress_time_windows_select_1_struct_out {
    ingress_time_windows_select_1_struct_out out;
    out.bidder = in.bidder;
    out.processed = in.COUNT;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto sink_4_op = Table_Sink_Builder<ingress_time_windows_select_1_struct_out>("ingress_time_windows",
    [](const ingress_time_windows_select_1_struct_out& record, std::ostream& os) {
 
    os << record.bidder << ",";
 
    os << record.processed;
}
)
    .withName("ingress_time_windows_sink_4")
    .withParallelism(2)
    .withHeader("bidder,processed")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "ingress_time_windows", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::INGRESS_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(window_group_2_op).add(select_3_op).add_sink(sink_4_op);

    topology.run();
    return 0;
}