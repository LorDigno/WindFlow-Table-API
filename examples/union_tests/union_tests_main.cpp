#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "union_tests_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_sensor_source_query_5_from_6>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sensor_source_query_5_from_6& record, uint64_t& timestamp) {
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
    .withName("sensor_source_query_5_from_6")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_2_op = Where_Builder<source_sensor_source_query_5_from_6>(
        [](const source_sensor_source_query_5_from_6& in) -> bool {
    return (in.temperature > 30);
}
    )
    .withName("sensor_source_query_5_where_5")
    .withParallelism(2)
    .build();

    auto select_3_op = Select_Builder<source_sensor_source_query_5_from_6, sensor_source_query_5_select_4_struct_out>(
        [](const source_sensor_source_query_5_from_6& in) -> sensor_source_query_5_select_4_struct_out {
    sensor_source_query_5_select_4_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto from_4_op = Table_Source_Builder<source_sensor_source_query_5_from_6>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sensor_source_query_5_from_6& record, uint64_t& timestamp) {
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
    .withName("sensor_source_query_6_from_9")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_5_op = Where_Builder<source_sensor_source_query_5_from_6>(
        [](const source_sensor_source_query_5_from_6& in) -> bool {
    return (in.temperature > 25);
}
    )
    .withName("sensor_source_query_6_where_8")
    .withParallelism(2)
    .build();

    auto select_6_op = Select_Builder<source_sensor_source_query_5_from_6, sensor_source_query_5_select_4_struct_out>(
        [](const source_sensor_source_query_5_from_6& in) -> sensor_source_query_5_select_4_struct_out {
    sensor_source_query_5_select_4_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_6_op")
    .withParallelism(2)
    .build();

    auto distinct_7_op = Distinct_Builder<sensor_source_query_5_select_4_struct_out, sensor_source_query_5_select_4_struct_out>()
    .withName("union_tests_union_3_distinct")   
    .withParallelism(2)  
    .withKeyBy([](const sensor_source_query_5_select_4_struct_out& in) -> sensor_source_query_5_select_4_struct_out { return in; })
    .build_keyed();


    auto from_8_op = Table_Source_Builder<source_sensor_source_query_5_from_6>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sensor_source_query_5_from_6& record, uint64_t& timestamp) {
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
    .withName("sensor_source_query_7_from_12")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto where_9_op = Where_Builder<source_sensor_source_query_5_from_6>(
        [](const source_sensor_source_query_5_from_6& in) -> bool {
    return (in.temperature < 15);
}
    )
    .withName("sensor_source_query_7_where_11")
    .withParallelism(2)
    .build();

    auto select_10_op = Select_Builder<source_sensor_source_query_5_from_6, sensor_source_query_5_select_4_struct_out>(
        [](const source_sensor_source_query_5_from_6& in) -> sensor_source_query_5_select_4_struct_out {
    sensor_source_query_5_select_4_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_10_op")
    .withParallelism(2)
    .build();

    auto select_11_op = Select_Builder<sensor_source_query_5_select_4_struct_out, sensor_source_query_5_select_4_struct_out>(
        [](const sensor_source_query_5_select_4_struct_out& in) -> sensor_source_query_5_select_4_struct_out {
    sensor_source_query_5_select_4_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    return out;
}
    )
    .withName("select_11_op")
    .withParallelism(2)
    .build();

    auto sink_12_op = Table_Sink_Builder<sensor_source_query_5_select_4_struct_out>("union_tests",
    [](const sensor_source_query_5_select_4_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.temperature;}
)
    .withName("union_tests_sink_13")
    .withParallelism(2)
    .withHeader("sensor_id,temperature")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "union_tests", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_2 = topology.add_source(from_1_op).add(where_2_op).add(select_3_op);

    auto& pipe_3 = topology.add_source(from_4_op).add(where_5_op).add(select_6_op);

    std::vector<wf::MultiPipe*> pipe_1_branches = {&pipe_2, &pipe_3};
auto* pipe_1_pointer = wf::merge_multipipes_func(&topology, pipe_1_branches);
auto& pipe_1 = (*pipe_1_pointer).add(distinct_7_op);

    auto& pipe_4 = topology.add_source(from_8_op).add(where_9_op).add(select_10_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_4};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(select_11_op).add_sink(sink_12_op);

    topology.run();
    return 0;
}