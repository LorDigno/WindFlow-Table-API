#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "specific_id_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t specific_id_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_specific_id_from_3>( "/home/user/TableAPI/data_streams/bid.csv",
    [](const std::string& line, source_specific_id_from_3& record, uint64_t& timestamp) {
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
    .withName("specific_id_from_3")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(specific_id_epoch)
    .build();

    auto where_2_op = Where_Builder<source_specific_id_from_3>(
        [](const source_specific_id_from_3& in) -> bool {
    return (((((in.auction_id == 1007) || (in.auction_id == 1020)) || (in.auction_id == 2001)) || (in.auction_id == 2019)) || (in.auction_id == 2087));
}
    )
    .withName("specific_id_where_2")
    .withParallelism(2)
    .build();

    auto select_3_op = Select_Builder<source_specific_id_from_3, specific_id_select_1_struct_out>(
        [](const source_specific_id_from_3& in) -> specific_id_select_1_struct_out {
    specific_id_select_1_struct_out out;
    out.auction_id = in.auction_id;
    out.price = in.price;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto sink_4_op = Table_Sink_Builder<specific_id_select_1_struct_out>("specific_id",
    [](const specific_id_select_1_struct_out& record, std::ostream& os) {
 
    os << record.auction_id << ",";
 
    os << record.price;
}
)
    .withName("specific_id_sink_4")
    .withParallelism(2)
    .withHeader("auction_id,price")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "specific_id", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(where_2_op).add(select_3_op).add_sink(sink_4_op);

    topology.run();
    return 0;
}