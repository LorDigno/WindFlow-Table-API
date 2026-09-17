#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "multiple_join_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t multiple_join_epoch = parse_ISO8601("2026-09-04T08:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_multiple_join_from_3>( "/home/user/TableAPI/data_streams/sensor_second_stream.csv",
    [](const std::string& line, source_multiple_join_from_3& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    //timestamp
    std::getline(ss, token, ',');
    timestamp = parse_ISO8601(token);
    //dati
    std::getline(ss, record.sensor_id, ',');
    std::getline(ss, token, ',');
    record.temp = parse_DOUBLE(token);
    std::getline(ss, token, ',');
    record.hum = parse_DOUBLE(token);
}
)
    .withName("multiple_join_from_3")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withDelayedEventTime(multiple_join_epoch, 180000000ULL)
    .build();

    auto from_2_op = Table_Source_Builder<source_multiple_join_from_4>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_multiple_join_from_4& record, uint64_t& timestamp) {
    std::stringstream ss(line);
    std::string token;

    //timestamp
    std::getline(ss, token, ',');
    timestamp = parse_ISO8601(token);
    //dati
    std::getline(ss, record.sensor_id, ',');
    std::getline(ss, token, ',');
    record.temperature = parse_DOUBLE(token);
    std::getline(ss, token, ',');
    record.humidity = parse_DOUBLE(token);
}
)
    .withName("multiple_join_from_4")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime(multiple_join_epoch)
    .build();

    auto left_unifier_3_op = Select_Builder<source_multiple_join_from_3, source_multiple_join_from_3_unified_source_multiple_join_from_4>(
        [](const source_multiple_join_from_3& in) -> source_multiple_join_from_3_unified_source_multiple_join_from_4 {
    source_multiple_join_from_3_unified_source_multiple_join_from_4 out;
    out.sensor_id = in.sensor_id;
    out.temp = in.temp;
    out.hum = in.hum;
    return out;
}
    )
    .withName("left_unifier_3_op")
    .withParallelism(2)
    .build();

    auto right_unifier_4_op = Select_Builder<source_multiple_join_from_4, source_multiple_join_from_3_unified_source_multiple_join_from_4>(
        [](const source_multiple_join_from_4& in) -> source_multiple_join_from_3_unified_source_multiple_join_from_4 {
    source_multiple_join_from_3_unified_source_multiple_join_from_4 out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.humidity = in.humidity;
    return out;
}
    )
    .withName("right_unifier_4_op")
    .withParallelism(2)
    .build();

    auto join_5_op = Table_Window_Join_Builder<source_multiple_join_from_3_unified_source_multiple_join_from_4, source_multiple_join_from_3_unified_source_multiple_join_from_4, multiple_join_join_window_2_key_struct>(
    [](const source_multiple_join_from_3_unified_source_multiple_join_from_4& left, const source_multiple_join_from_3_unified_source_multiple_join_from_4& right) -> source_multiple_join_from_3_unified_source_multiple_join_from_4 {
    source_multiple_join_from_3_unified_source_multiple_join_from_4 out;
    out.sensor_id = left.sensor_id;
    out.temp = left.temp;
    out.hum = left.hum;
    out.temperature = right.temperature;
    out.humidity = right.humidity;
    return out;
}
)
    .withName("multiple_join_join_window_2")
    .withTBWindow(240000000ULL, 120000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_multiple_join_from_3_unified_source_multiple_join_from_4& in) -> multiple_join_join_window_2_key_struct {
    multiple_join_join_window_2_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto sink_6_op = Table_Sink_Builder<source_multiple_join_from_3_unified_source_multiple_join_from_4>("multiple_join",
    [](const source_multiple_join_from_3_unified_source_multiple_join_from_4& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.temp << ","; os << record.hum << ","; os << record.temperature << ","; os << record.humidity;}
)
    .withName("multiple_join_sink_5")
    .withParallelism(2)
    .withHeader("sensor_id,temp,hum,temperature,humidity")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "multiple_join", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(left_unifier_3_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(right_unifier_4_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_5_op).add_sink(sink_6_op);

    topology.run();
    return 0;
}