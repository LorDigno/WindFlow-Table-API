#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <fstream>
#include <sstream>
#include <chrono>
#include <windflow.hpp>
#include <windflow_table_api.hpp>
#include "avg_cold_temperature_structs.hpp"

int main(int argc, char* argv[]) {
    //-----     OPERATOR BUILDERS   -----

    auto where_1_op = Where_Builder<source_cold_and_dry_from_6>(
        [](const source_cold_and_dry_from_6& in) -> bool {
    return ((in.temperature < 10) && (in.humidity < 20));
}
    )
    .withName("cold_and_dry_where_5")
    .withParallelism(2)
    .build();

    auto distinct_2_op = Distinct_Builder<source_cold_and_dry_from_6, source_cold_and_dry_from_6>()
    .withName("cold_and_dry_distinct_4")
    .withParallelism(2)     
    .withKeyBy([](const source_cold_and_dry_from_6& in) -> source_cold_and_dry_from_6{ return in; })
    .build_keyed();


    auto select_3_op = Select_Builder<source_cold_and_dry_from_6, source_cold_and_dry_from_6>(
        [](const source_cold_and_dry_from_6& in) -> source_cold_and_dry_from_6 {
    source_cold_and_dry_from_6 out;
    out.sensor_id = in.sensor_id;
    out.temperature = in.temperature;
    out.humidity = in.humidity;
    return out;
}
    )
    .withName("cold_and_dry_select_3")
    .withParallelism(2)
    .build();

    auto group_4_op = Global_Group_Builder<source_cold_and_dry_from_6, avg_cold_temperature_group_by_2_struct_out>(
    [](const source_cold_and_dry_from_6& in, avg_cold_temperature_group_by_2_struct_out& out) -> void {

    out.COUNT_ += 1;
    out.SUM_temperature += in.temperature;
    out.AVG_temperature = out.SUM_temperature / out.COUNT_ ;
}
)
    .withName("avg_cold_temperature_group_by_2")
    .withParallelism(2)
    .build();


    auto select_5_op = Select_Builder<avg_cold_temperature_group_by_2_struct_out, avg_cold_temperature_select_1_struct_out>(
        [](const avg_cold_temperature_group_by_2_struct_out& in) -> avg_cold_temperature_select_1_struct_out {
    avg_cold_temperature_select_1_struct_out out;
    out.avg_temp = in.AVG_temperature;
    return out;
}
    )
    .withName("avg_cold_temperature_select_1")
    .withParallelism(2)
    .build();

    //-----     PIPES AND TOPOLOGY  ------
    wf::PipeGraph topology(
        "avg_cold_temperature", 
        wf::Execution_Mode_t::DEFAULT
        , wf::Time_Policy_t::EVENT_TIME 
    );

    auto& pipe_0 = topology.add_source(***).add(where_1_op).add(distinct_2_op).add(select_3_op).add(group_4_op).add(select_5_op).add_sink(***);

    topology.run();
    return 0;
}