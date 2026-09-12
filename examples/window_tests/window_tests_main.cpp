#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "window_tests_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_window_tests_from_4>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_window_tests_from_4& record, uint64_t& timestamp) {
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
    .withName("window_tests_from_4")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto from_2_op = Table_Source_Builder<source_window_tests_from_4>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_window_tests_from_4& record, uint64_t& timestamp) {
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
    .withName("renamed_src_from_6")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto select_3_op = Select_Builder<source_window_tests_from_4, renamed_src_select_5_struct_out>(
        [](const source_window_tests_from_4& in) -> renamed_src_select_5_struct_out {
    renamed_src_select_5_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temp = in.temperature;
    out.hum = in.humidity;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto left_unifier_4_op = Select_Builder<source_window_tests_from_4, source_window_tests_from_4_unified_renamed_src_select_5_struct_out>(
        [](const source_window_tests_from_4& in) -> source_window_tests_from_4_unified_renamed_src_select_5_struct_out {
    source_window_tests_from_4_unified_renamed_src_select_5_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.humidity = in.humidity;
    return out;
}
    )
    .withName("left_unifier_4_op")
    .withParallelism(2)
    .build();

    auto right_unifier_5_op = Select_Builder<renamed_src_select_5_struct_out, source_window_tests_from_4_unified_renamed_src_select_5_struct_out>(
        [](const renamed_src_select_5_struct_out& in) -> source_window_tests_from_4_unified_renamed_src_select_5_struct_out {
    source_window_tests_from_4_unified_renamed_src_select_5_struct_out out;
    out.sensor_id = in.sensor_id;
    out.temp = in.temp;
    out.hum = in.hum;
    return out;
}
    )
    .withName("right_unifier_5_op")
    .withParallelism(2)
    .build();

    auto join_6_op = Table_Window_Join_Builder<source_window_tests_from_4_unified_renamed_src_select_5_struct_out, source_window_tests_from_4_unified_renamed_src_select_5_struct_out, window_tests_join_window_3_key_struct>(
    [](const source_window_tests_from_4_unified_renamed_src_select_5_struct_out& left, const source_window_tests_from_4_unified_renamed_src_select_5_struct_out& right) -> source_window_tests_from_4_unified_renamed_src_select_5_struct_out {
    source_window_tests_from_4_unified_renamed_src_select_5_struct_out out;
    out.sensor_id = left.sensor_id;
    out.temperature = left.temperature;
    out.humidity = left.humidity;
    out.temp = right.temp;
    out.hum = right.hum;
    return out;
}
)
    .withName("window_tests_join_window_3")
    .withTBWindow(600000000ULL, 300000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_window_tests_from_4_unified_renamed_src_select_5_struct_out& in) -> window_tests_join_window_3_key_struct {
    window_tests_join_window_3_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto window_group_7_op = Windowed_Group_Builder<source_window_tests_from_4_unified_renamed_src_select_5_struct_out, window_tests_window_group_by_2_struct_out, window_tests_join_window_3_key_struct>(
    [](const source_window_tests_from_4_unified_renamed_src_select_5_struct_out& in, window_tests_window_group_by_2_struct_out& out) -> void {
    out.sensor_id = in.sensor_id;

    out.COUNT += 1;
    out.SUM_temperature += in.temperature;
    out.AVG_temperature = out.SUM_temperature / out.COUNT ;
}
)
    .withName("window_tests_window_group_by_2")
    .withTBWindow(600000000ULL, 300000000ULL)
    .withParallelism(2)
    .withKeyBy([](const source_window_tests_from_4_unified_renamed_src_select_5_struct_out& in) -> window_tests_join_window_3_key_struct {
    window_tests_join_window_3_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto select_8_op = Select_Builder<window_tests_window_group_by_2_struct_out, window_tests_select_1_struct_out>(
        [](const window_tests_window_group_by_2_struct_out& in) -> window_tests_select_1_struct_out {
    window_tests_select_1_struct_out out;
    out.sensor_id = in.sensor_id;
    out.media = in.AVG_temperature;
    return out;
}
    )
    .withName("select_8_op")
    .withParallelism(2)
    .build();

    auto sink_9_op = Table_Sink_Builder<window_tests_select_1_struct_out>("window_tests",
    [](const window_tests_select_1_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.media;}
)
    .withName("window_tests_sink_7")
    .withParallelism(2)
    .withHeader("sensor_id,media")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "window_tests", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_1 = topology.add_source(from_1_op).add(left_unifier_4_op);

    auto& pipe_2 = topology.add_source(from_2_op).add(select_3_op).add(right_unifier_5_op);

    std::vector<wf::MultiPipe*> pipe_0_branches = {&pipe_1, &pipe_2};
auto* pipe_0_pointer = wf::merge_multipipes_func(&topology, pipe_0_branches);
auto& pipe_0 = (*pipe_0_pointer).add(join_6_op).add(window_group_7_op).add(select_8_op).add_sink(sink_9_op);

    topology.run();
    return 0;
}