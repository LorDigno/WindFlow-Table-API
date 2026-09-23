#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "keyless_interval_join_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t keyless_interval_join_epoch = parse_ISO8601("2026-09-04T08:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_keyless_interval_join_from_3>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_keyless_interval_join_from_3& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    std::getline(ss, token, ',');
    record.timestamp = parse_ISO8601(token);
    timestamp = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.sensor_id = parse_STRING(token);

    std::getline(ss, token, ',');
    record.temperature = parse_DOUBLE(token);

    std::getline(ss, token, ',');
    record.humidity = parse_DOUBLE(token);

}
)
    .withName("keyless_interval_join_from_3")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime(keyless_interval_join_epoch)
    .build();

    auto from_2_op = Table_Source_Builder<source_keyless_interval_join_from_3>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_keyless_interval_join_from_3& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    std::getline(ss, token, ',');
    record.timestamp = parse_ISO8601(token);
    timestamp = parse_ISO8601(token);

    std::getline(ss, token, ',');
    record.sensor_id = parse_STRING(token);

    std::getline(ss, token, ',');
    record.temperature = parse_DOUBLE(token);

    std::getline(ss, token, ',');
    record.humidity = parse_DOUBLE(token);

}
)
    .withName("rerenamed_src_from_5")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime(keyless_interval_join_epoch)
    .build();

    auto select_3_op = Select_Builder<source_keyless_interval_join_from_3, rerenamed_src_select_4_struct_out>(
        [](const source_keyless_interval_join_from_3& in) -> rerenamed_src_select_4_struct_out {
    rerenamed_src_select_4_struct_out out;
    out.ts = in.timestamp;
    out.sens = in.sensor_id;
    out.temp = in.temperature;
    out.hum = in.humidity;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto left_unifier_4_op = Select_Builder<source_keyless_interval_join_from_3, source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out>(
        [](const source_keyless_interval_join_from_3& in) -> source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out {
    source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out out;
    out.timestamp = in.timestamp;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.humidity = in.humidity;
    return out;
}
    )
    .withName("left_unifier_4_op")
    .withParallelism(2)
    .build();

    auto right_unifier_5_op = Select_Builder<rerenamed_src_select_4_struct_out, source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out>(
        [](const rerenamed_src_select_4_struct_out& in) -> source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out {
    source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out out;
    out.ts = in.ts;
    out.sens = in.sens;
    out.temp = in.temp;
    out.hum = in.hum;
    return out;
}
    )
    .withName("right_unifier_5_op")
    .withParallelism(2)
    .build();

    auto join_6_op = Table_Interval_Join_Builder<source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out, source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out>(
    [](const source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out& left, const source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out& right) -> std::optional<source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out> {

    source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out out{};
    out.timestamp = left.timestamp;
    out.sensor_id = left.sensor_id;
    out.temperature = left.temperature;
    out.humidity = left.humidity;
    out.ts = right.ts;
    out.sens = right.sens;
    out.temp = right.temp;
    out.hum = right.hum;
    return out;
},
    -300000000,
    300000000
)
    .withName("keyless_interval_join_join_interval_2")
    .withParallelism(2)
    .build();


    auto select_7_op = Select_Builder<source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out, keyless_interval_join_select_1_struct_out>(
        [](const source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out& in) -> keyless_interval_join_select_1_struct_out {
    keyless_interval_join_select_1_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.sens = in.sens;
    out.hum = in.hum;
    out.timestamp = in.timestamp;
    out.ts = in.ts;
    return out;
}
    )
    .withName("select_7_op")
    .withParallelism(2)
    .build();

    auto sink_8_op = Table_Sink_Builder<keyless_interval_join_select_1_struct_out>("keyless_interval_join",
    [](const keyless_interval_join_select_1_struct_out& record, std::ostream& os) {
 
    os << record.sensor_id << ",";
 
    os << record.temperature << ",";
 
    os << record.sens << ",";
 
    os << record.hum << ",";
 
    os << reformat_ISO8601(record.timestamp) << ",";
 
    os << reformat_ISO8601(record.ts);
}
)
    .withName("keyless_interval_join_sink_6")
    .withParallelism(2)
    .withHeader("sensor_id,temperature,sens,hum,timestamp,ts")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "keyless_interval_join", 
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