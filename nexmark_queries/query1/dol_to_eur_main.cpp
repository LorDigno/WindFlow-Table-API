#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "dol_to_eur_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t dol_to_eur_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_dol_to_eur_from_2>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/bid.csv",
    [](const std::string& line, source_dol_to_eur_from_2& record, uint64_t& timestamp) {
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
    .withName("dol_to_eur_from_2")
    .withHeader()
    .withParallelism(2, 5242880ULL)
    .withOrderedEventTime(dol_to_eur_epoch)
    .build();

    auto select_2_op = Select_Builder<source_dol_to_eur_from_2, dol_to_eur_select_1_struct_out>(
        [](const source_dol_to_eur_from_2& in) -> dol_to_eur_select_1_struct_out {
    dol_to_eur_select_1_struct_out out;
    out.auction_id = in.auction_id;
    out.price_eur = (in.price * 0.87);
    out.bidder = in.bidder;
    out.bid_dateTime = in.bid_dateTime;
    return out;
}
    )
    .withName("select_2_op")
    .withParallelism(2)
    .build();

    auto sink_3_op = Table_Sink_Builder<dol_to_eur_select_1_struct_out>("dol_to_eur",
    [](const dol_to_eur_select_1_struct_out& record, std::ostream& os) {
 
    os << record.auction_id << ",";
 
    os << record.price_eur << ",";
 
    os << record.bidder << ",";
 
    os << reformat_ISO8601(record.bid_dateTime);
}
)
    .withName("dol_to_eur_sink_3")
    .withParallelism(2)
    .withHeader("auction_id,price_eur,bidder,bid_dateTime")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "dol_to_eur", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(select_2_op).add_sink(sink_3_op);

    topology.run();
    return 0;
}