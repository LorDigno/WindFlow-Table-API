#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "self_interval_join_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_self_interval_join_from_3>( "sensor_real_stream.csv",
    [](const std::string& line, source_self_interval_join_from_3& record, uint64_t& timestamp) {
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
    .withName("self_interval_join_from_3")
    .withHeader()
    .withParallelism(2, 300ULL)
    .withWatermarkDelay(7200000000ULL)
    .build();

    auto from_2_op = Table_Source_Builder<source_self_interval_join_from_3>( "sensor_real_stream.csv",
    [](const std::string& line, source_self_interval_join_from_3& record, uint64_t& timestamp) {
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
    .withName("renaming_for_selfjoin_from_5")
    .withHeader()
    .withParallelism(2, 300ULL)
    .withWatermarkDelay(7200000000ULL)
    .build();

    auto select_3_op = Select_Builder<source_self_interval_join_from_3, renaming_for_selfjoin_select_4_struct_out>(
        [](const source_self_interval_join_from_3& in) -> renaming_for_selfjoin_select_4_struct_out {
    renaming_for_selfjoin_select_4_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temp = in.temperature;
    out.hum = in.humidity;
    return out;
}
    )
    .withName("renaming_for_selfjoin_select_4")
    .withParallelism(2)
    .build();

    auto map_4_op = Select_Builder<source_self_interval_join_from_3, self_interval_join_join_interval_2_struct_out>(
        [](const source_self_interval_join_from_3& in) -> self_interval_join_join_interval_2_struct_out {
    self_interval_join_join_interval_2_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.humidity = in.humidity;
    return out;
}
    )
    .withName("self_interval_join_join_interval_2_left_unifier")
    .withParallelism(2)
    .build();

    auto map_5_op = Select_Builder<renaming_for_selfjoin_select_4_struct_out, self_interval_join_join_interval_2_struct_out>(
        [](const renaming_for_selfjoin_select_4_struct_out& in) -> self_interval_join_join_interval_2_struct_out {
    self_interval_join_join_interval_2_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temp = in.temp;
    out.hum = in.hum;
    return out;
}
    )
    .withName("self_interval_join_join_interval_2_right_unifier")
    .withParallelism(2)
    .build();

    auto join_6_op = Table_Interval_Join_Builder<self_interval_join_join_interval_2_struct_out, self_interval_join_join_interval_2_struct_out, self_interval_join_join_interval_2_key_struct>(
    [](const self_interval_join_join_interval_2_struct_out& left, const self_interval_join_join_interval_2_struct_out& right) -> self_interval_join_join_interval_2_struct_out {
    self_interval_join_join_interval_2_struct_out out;
    out.sensor_id = left.sensor_id;
    out.temperature = left.temperature;
    out.humidity = left.humidity;
    out.temp = right.temp;
    out.hum = right.hum;
    return out;
},
    -1800000000,
    1800000000
)
    .withName("self_interval_join_join_interval_2")
    .withParallelism(2)
    .withKeyBy([](const self_interval_join_join_interval_2_struct_out& in) -> self_interval_join_join_interval_2_key_struct {
    self_interval_join_join_interval_2_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto select_7_op = Select_Builder<self_interval_join_join_interval_2_struct_out, self_interval_join_select_1_struct_out>(
        [](const self_interval_join_join_interval_2_struct_out& in) -> self_interval_join_select_1_struct_out {
    self_interval_join_select_1_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.hum = in.hum;
    return out;
}
    )
    .withName("self_interval_join_select_1")
    .withParallelism(2)
    .build();

    auto sink_8_op = Table_Sink_Builder<self_interval_join_select_1_struct_out>("self_interval_join_output.csv",
    [](const self_interval_join_select_1_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.temperature << ","; os << record.hum;}
)
    .withName("self_interval_join_sink")
    .withParallelism(2)
    .withHeader("sensor_id, temperature, hum")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "self_interval_join", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(map_4_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(select_3_op).add(map_5_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_6_op).add(select_7_op).add_sink(sink_8_op);

    topology.run();
    return 0;
}