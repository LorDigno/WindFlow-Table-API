#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "unary_simple_test_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_unary_simple_test_from_5>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_unary_simple_test_from_5& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    //timestamp
    std::getline(ss, token, ',');
    timestamp = parse_TIMESTAMP_ISO8601(token);
    //dati
    std::getline(ss, record.sensor_id, ',');
    std::getline(ss, token, ',');
    record.temperature = parse_DOUBLE(token);
    std::getline(ss, token, ',');
    record.humidity = parse_DOUBLE(token);
}
)
    .withName("unary_simple_test_from_5")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_2_op = Where_Builder<source_unary_simple_test_from_5>(
        [](const source_unary_simple_test_from_5& in) -> bool {
    return (in.temperature > 30);
}
    )
    .withName("unary_simple_test_where_4")
    .withParallelism(2)
    .build();

    auto distinct_3_op = Distinct_Builder<source_unary_simple_test_from_5, source_unary_simple_test_from_5>()
    .withName("unary_simple_test_distinct_3")   
    .withParallelism(2)  
    .withKeyBy([](const source_unary_simple_test_from_5& in) -> source_unary_simple_test_from_5 { return in; })
    .build_keyed();


    auto global_group_4_op = Global_Group_Builder<source_unary_simple_test_from_5, unary_simple_test_global_group_by_2_struct_out, unary_simple_test_global_group_by_2_key_struct>(
    [](const source_unary_simple_test_from_5& in, unary_simple_test_global_group_by_2_struct_out& out) -> void {
    out.sensor_id = in.sensor_id;

    out.COUNT += 1;
}
)
    .withName("unary_simple_test_global_group_by_2")
    .withParallelism(2)
    .withKeyBy([](const source_unary_simple_test_from_5& in) -> unary_simple_test_global_group_by_2_key_struct {
    unary_simple_test_global_group_by_2_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto select_5_op = Select_Builder<unary_simple_test_global_group_by_2_struct_out, unary_simple_test_select_1_struct_out>(
        [](const unary_simple_test_global_group_by_2_struct_out& in) -> unary_simple_test_select_1_struct_out {
    unary_simple_test_select_1_struct_out out;
    out.sensor_id = in.sensor_id;
    out.conteggio = in.COUNT;
    return out;
}
    )
    .withName("select_5_op")
    .withParallelism(2)
    .build();

    auto sink_6_op = Table_Sink_Builder<unary_simple_test_select_1_struct_out>("unary_simple_test",
    [](const unary_simple_test_select_1_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.conteggio;}
)
    .withName("unary_simple_test_sink_6")
    .withParallelism(2)
    .withHeader("sensor_id,conteggio")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "unary_simple_test", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(where_2_op).add(distinct_3_op).add(global_group_4_op).add(select_5_op).add_sink(sink_6_op);

    topology.run();
    return 0;
}