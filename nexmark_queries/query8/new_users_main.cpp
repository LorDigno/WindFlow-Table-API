#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "new_users_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t new_users_epoch = parse_ISO8601("2026-09-01T00:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_new_users_from_3>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/person.csv",
    [](const std::string& line, source_new_users_from_3& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    std::getline(ss, token, ',');
    record.person_id = parse_BIGINT(token);

    std::getline(ss, token, ',');
    record.name = parse_STRING(token);

    std::getline(ss, token, ',');
    record.email_address = parse_STRING(token);

    std::getline(ss, token, ',');
    record.credit_card = parse_STRING(token);

    std::getline(ss, token, ',');
    record.city = parse_STRING(token);

    std::getline(ss, token, ',');
    record.state = parse_STRING(token);

    std::getline(ss, token, ',');
    record.person_dateTime = parse_ISO8601(token);
    timestamp = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.extra = parse_STRING(token);

}
)
    .withName("new_users_from_3")
    .withHeader()
    .withParallelism(2, 409600ULL)
    .withOrderedEventTime(new_users_epoch)
    .build();

    auto from_2_op = Table_Source_Builder<source_auction_source_query_4_from_5>( "/disc1/homes/lorenzoni/WindFlow-Table-API/data_streams/auction.csv",
    [](const std::string& line, source_auction_source_query_4_from_5& record, uint64_t& timestamp) {
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
    .withName("auction_source_query_4_from_5")
    .withHeader()
    .withParallelism(2, 512000ULL)
    .withOrderedEventTime(new_users_epoch)
    .build();

    auto select_3_op = Select_Builder<source_auction_source_query_4_from_5, auction_source_query_4_select_4_struct_out>(
        [](const source_auction_source_query_4_from_5& in) -> auction_source_query_4_select_4_struct_out {
    auction_source_query_4_select_4_struct_out out;
    out.auction_id = in.auction_id;
    out.item_name = in.item_name;
    out.description = in.description;
    out.initial_bid = in.initial_bid;
    out.reserve = in.reserve;
    out.auction_dateTime = in.auction_dateTime;
    out.expires = in.expires;
    out.person_id = in.seller;
    out.category = in.category;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto left_unifier_4_op = Select_Builder<source_new_users_from_3, source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out>(
        [](const source_new_users_from_3& in) -> source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out {
    source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out out;
    out.person_id = in.person_id;
    out.name = in.name;
    out.email_address = in.email_address;
    out.credit_card = in.credit_card;
    out.city = in.city;
    out.state = in.state;
    out.person_dateTime = in.person_dateTime;
    out.extra = in.extra;
    return out;
}
    )
    .withName("left_unifier_4_op")
    .withParallelism(2)
    .build();

    auto right_unifier_5_op = Select_Builder<auction_source_query_4_select_4_struct_out, source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out>(
        [](const auction_source_query_4_select_4_struct_out& in) -> source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out {
    source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out out;
    out.auction_id = in.auction_id;
    out.item_name = in.item_name;
    out.description = in.description;
    out.initial_bid = in.initial_bid;
    out.reserve = in.reserve;
    out.auction_dateTime = in.auction_dateTime;
    out.expires = in.expires;
    out.person_id = in.person_id;
    out.category = in.category;
    return out;
}
    )
    .withName("right_unifier_5_op")
    .withParallelism(2)
    .build();

    auto join_6_op = Table_Interval_Join_Builder<source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out, source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out, new_users_join_interval_2_key_struct>(
    [](const source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out& left, const source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out& right) -> std::optional<source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out> {

    source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out out{};
    out.person_id = left.person_id;
    out.name = left.name;
    out.email_address = left.email_address;
    out.credit_card = left.credit_card;
    out.city = left.city;
    out.state = left.state;
    out.person_dateTime = left.person_dateTime;
    out.extra = left.extra;
    out.auction_id = right.auction_id;
    out.item_name = right.item_name;
    out.description = right.description;
    out.initial_bid = right.initial_bid;
    out.reserve = right.reserve;
    out.auction_dateTime = right.auction_dateTime;
    out.expires = right.expires;
    out.category = right.category;
    return out;
},
    -60000000,
    43200000000
)
    .withName("new_users_join_interval_2")
    .withParallelism(2)
    .withKeyBy([](const source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out& in) -> new_users_join_interval_2_key_struct {
    new_users_join_interval_2_key_struct out;
    out.person_id = in.person_id;
    return out;
})
    .build_keyed();


    auto select_7_op = Select_Builder<source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out, new_users_select_1_struct_out>(
        [](const source_new_users_from_3_unified_auction_source_query_4_select_4_struct_out& in) -> new_users_select_1_struct_out {
    new_users_select_1_struct_out out;
    out.person_id = in.person_id;
    out.name = in.name;
    out.auction_id = in.auction_id;
    out.reserve = in.reserve;
    return out;
}
    )
    .withName("select_7_op")
    .withParallelism(2)
    .build();

    auto sink_8_op = Table_Sink_Builder<new_users_select_1_struct_out>("new_users",
    [](const new_users_select_1_struct_out& record, std::ostream& os) {
 
    os << record.person_id << ",";
 
    os << record.name << ",";
 
    os << record.auction_id << ",";
 
    os << record.reserve;
}
)
    .withName("new_users_sink_6")
    .withParallelism(2)
    .withHeader("person_id,name,auction_id,reserve")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "new_users", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(left_unifier_4_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(select_3_op).add(right_unifier_5_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_6_op).add(select_7_op).add_sink(sink_8_op);

    topology.run();
    return 0;
}