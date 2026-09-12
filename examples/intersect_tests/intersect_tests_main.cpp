#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "intersect_tests_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_sensor_source_query_5_from_5>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sensor_source_query_5_from_5& record, uint64_t& timestamp) {
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
    .withName("sensor_source_query_5_from_5")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_2_op = Where_Builder<source_sensor_source_query_5_from_5>(
        [](const source_sensor_source_query_5_from_5& in) -> bool {
    return (in.temperature > 30);
}
    )
    .withName("sensor_source_query_5_where_4")
    .withParallelism(2)
    .build();

    auto select_3_op = Select_Builder<source_sensor_source_query_5_from_5, sensor_source_query_5_select_3_struct_out>(
        [](const source_sensor_source_query_5_from_5& in) -> sensor_source_query_5_select_3_struct_out {
    sensor_source_query_5_select_3_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto from_4_op = Table_Source_Builder<source_sensor_source_query_5_from_5>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sensor_source_query_5_from_5& record, uint64_t& timestamp) {
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
    .withName("sensor_source_query_6_from_8")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_5_op = Where_Builder<source_sensor_source_query_5_from_5>(
        [](const source_sensor_source_query_5_from_5& in) -> bool {
    return (in.temperature > 25);
}
    )
    .withName("sensor_source_query_6_where_7")
    .withParallelism(2)
    .build();

    auto select_6_op = Select_Builder<source_sensor_source_query_5_from_5, sensor_source_query_5_select_3_struct_out>(
        [](const source_sensor_source_query_5_from_5& in) -> sensor_source_query_5_select_3_struct_out {
    sensor_source_query_5_select_3_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_6_op")
    .withParallelism(2)
    .build();

    auto left_tagger_7_op = Select_Builder<sensor_source_query_5_select_3_struct_out, Tagged_Tuple<sensor_source_query_5_select_3_struct_out>>(
        [](const sensor_source_query_5_select_3_struct_out& in) -> Tagged_Tuple<sensor_source_query_5_select_3_struct_out> {
    Tagged_Tuple<sensor_source_query_5_select_3_struct_out> out;
    out.data = in;
    out.tag = 0;
    return out;
}
    )
    .withName("left_tagger_7_op")
    .withParallelism(2)
    .build();

    auto right_tagger_8_op = Select_Builder<sensor_source_query_5_select_3_struct_out, Tagged_Tuple<sensor_source_query_5_select_3_struct_out>>(
        [](const sensor_source_query_5_select_3_struct_out& in) -> Tagged_Tuple<sensor_source_query_5_select_3_struct_out> {
    Tagged_Tuple<sensor_source_query_5_select_3_struct_out> out;
    out.data = in;
    out.tag = 1;
    return out;
}
    )
    .withName("right_tagger_8_op")
    .withParallelism(2)
    .build();

    auto intersect_9_op = Intersect_Builder<sensor_source_query_5_select_3_struct_out>()
    .withName("intersect_tests_intersect_2")
    .withParallelism(2)
    .build_keyed();


    auto select_10_op = Select_Builder<sensor_source_query_5_select_3_struct_out, sensor_source_query_5_select_3_struct_out>(
        [](const sensor_source_query_5_select_3_struct_out& in) -> sensor_source_query_5_select_3_struct_out {
    sensor_source_query_5_select_3_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_10_op")
    .withParallelism(2)
    .build();

    auto sink_11_op = Table_Sink_Builder<sensor_source_query_5_select_3_struct_out>("intersect_tests",
    [](const sensor_source_query_5_select_3_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.temperature;}
)
    .withName("intersect_tests_sink_9")
    .withParallelism(2)
    .withHeader("sensor_id,temperature")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "intersect_tests", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(where_2_op).add(select_3_op).chain(left_tagger_7_op);

    auto& pipe_2 = topology.add_source(from_4_op).add(where_5_op).add(select_6_op).chain(right_tagger_8_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(intersect_9_op).add(select_10_op).add_sink(sink_11_op);

    topology.run();
    return 0;
}