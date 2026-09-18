#ifndef SELF_THETA_JOIN_STRUCTS_HPP
#define SELF_THETA_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_self_theta_join_from_3
// ============================================================================
struct source_self_theta_join_from_3 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: renaming_for_self_join_select_4_struct_out
// ============================================================================
struct renaming_for_self_join_select_4_struct_out {
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: source_self_theta_join_from_3_unified_renaming_for_self_join_select_4_struct_out
// ============================================================================
struct source_self_theta_join_from_3_unified_renaming_for_self_join_select_4_struct_out {
    std::string sensor_id;
    double temperature;
    double humidity;
    std::string sens;
    double temp;
    double hum;


};


// ============================================================================
// Struct: self_theta_join_select_1_struct_out
// ============================================================================
struct self_theta_join_select_1_struct_out {
    std::string sensor_id;
    std::string sens;
    double temperature;
    double hum;


};


#endif // SELF_THETA_JOIN_STRUCTS_HPP