#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "keyless_window_group_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_keyless_window_group_from_3>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_keyless_window_group_from_3& record, uint64_t& timestamp) {
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
    .withName("keyless_window_group_from_3")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime()
    .build();

    auto window_group_2_op = Windowed_Group_Builder<source_keyless_window_group_from_3, keyless_window_group_window_group_by_2_struct_out>(
    [](const source_keyless_window_group_from_3& in, keyless_window_group_window_group_by_2_struct_out& out) -> void {

    out.COUNT += 1;
}
)
    .withName("keyless_window_group_window_group_by_2")
    .withTBWindow(600000000ULL, 300000000ULL)
    .build();


    auto select_3_op = Select_Builder<keyless_window_group_window_group_by_2_struct_out, keyless_window_group_select_1_struct_out>(
        [](const keyless_window_group_window_group_by_2_struct_out& in) -> keyless_window_group_select_1_struct_out {
    keyless_window_group_select_1_struct_out out;
    out.conteggio = in.COUNT;
    return out;
}
    )
    .withName("select_3_op")
    .withParallelism(2)
    .build();

    auto sink_4_op = Table_Sink_Builder<keyless_window_group_select_1_struct_out>("keyless_window_group",
    [](const keyless_window_group_select_1_struct_out& record, std::ostream& os) {
 os << record.conteggio;}
)
    .withName("keyless_window_group_sink_4")
    .withParallelism(2)
    .withHeader("conteggio")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "keyless_window_group", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(window_group_2_op).add(select_3_op).add_sink(sink_4_op);

    topology.run();
    return 0;
}