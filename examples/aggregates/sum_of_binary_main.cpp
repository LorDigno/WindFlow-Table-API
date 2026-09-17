#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "sum_of_binary_structs.hpp"

int main(int argc, char* argv[]) {
    //variabile di epoch per la normalizzazione dei timestamp
    uint64_t sum_of_binary_epoch = parse_ISO8601("2026-09-04T08:00:00.000Z");

    //-----     OPERATOR BUILDERS   -----

    auto from_1_op = Table_Source_Builder<source_sum_of_binary_from_3>( "/home/user/TableAPI/data_streams/sensor_input_stream.csv",
    [](const std::string& line, source_sum_of_binary_from_3& record, uint64_t& timestamp) {
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
    .withName("sum_of_binary_from_3")
    .withHeader()
    .withParallelism(2, 0ULL)
    .withOrderedEventTime(sum_of_binary_epoch)
    .build();

    auto global_group_2_op = Global_Group_Builder<source_sum_of_binary_from_3, sum_of_binary_global_group_by_2_struct_out, sum_of_binary_global_group_by_2_key_struct>(
    [](const source_sum_of_binary_from_3& in, sum_of_binary_global_group_by_2_struct_out& out) -> void {
    out.sensor_id = in.sensor_id;

    out.SUM_temperature_+_humidity += (in.temperature + in.humidity);
}
)
    .withName("sum_of_binary_global_group_by_2")
    .withParallelism(2)
    .withKeyBy([](const source_sum_of_binary_from_3& in) -> sum_of_binary_global_group_by_2_key_struct {
    sum_of_binary_global_group_by_2_key_struct out;
    out.sensor_id = in.sensor_id;
    return out;
})
    .build_keyed();


    auto sink_3_op = Table_Sink_Builder<sum_of_binary_global_group_by_2_struct_out>("sum_of_binary",
    [](const sum_of_binary_global_group_by_2_struct_out& record, std::ostream& os) {
 os << record.sensor_id << ","; os << record.SUM_temperature_+_humidity;}
)
    .withName("sum_of_binary_sink_4")
    .withParallelism(2)
    .withHeader("sensor_id,SUM_temperature_+_humidity")
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "sum_of_binary", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(from_1_op).add(global_group_2_op).add_sink(sink_3_op);

    topology.run();
    return 0;
}