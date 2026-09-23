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
    uint64_t timestamp;
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: rerenamed_src_select_4_struct_out
// ============================================================================
struct rerenamed_src_select_4_struct_out {
    uint64_t ts;
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out
// ============================================================================
struct source_keyless_interval_join_from_3_unified_rerenamed_src_select_4_struct_out {
    uint64_t timestamp;
    std::string sensor_id;
    double temperature;
    double humidity;
    uint64_t ts;
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: keyless_interval_join_select_1_struct_out
// ============================================================================
struct keyless_interval_join_select_1_struct_out {
    std::string sensor_id;
    double temperature;
    std::string sens;
    double hum;
    uint64_t timestamp;
    uint64_t ts;


};


#endif // KEYLESS_INTERVAL_JOIN_STRUCTS_HPP