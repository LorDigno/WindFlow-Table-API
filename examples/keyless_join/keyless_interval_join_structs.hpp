#ifndef KEYLESS_INTERVAL_JOIN_STRUCTS_HPP
#define KEYLESS_INTERVAL_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_keyless_interval_join_from_3
// ============================================================================
struct source_keyless_interval_join_from_3 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: rerenamed_src_select_4_struct_out
// ============================================================================
struct rerenamed_src_select_4_struct_out {
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out
// ============================================================================
struct source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out {
    std::string sensor_id;
    double temperature;
    double humidity;
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: keyless_interval_join_select_1_struct_out
// ============================================================================
struct keyless_interval_join_select_1_struct_out {
    std::string sensor_id;
    double hum;
    double temperature;


};


#endif // KEYLESS_INTERVAL_JOIN_STRUCTS_HPP