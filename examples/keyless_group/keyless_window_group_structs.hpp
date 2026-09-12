#ifndef KEYLESS_WINDOW_GROUP_STRUCTS_HPP
#define KEYLESS_WINDOW_GROUP_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_keyless_window_group_from_3
// ============================================================================
struct source_keyless_window_group_from_3 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: keyless_window_group_window_group_by_2_struct_out
// ============================================================================
struct keyless_window_group_window_group_by_2_struct_out {
    int64_t COUNT = 0; 
    uint64_t win_id = 0; 

    keyless_window_group_window_group_by_2_struct_out() = default;

    keyless_window_group_window_group_by_2_struct_out(uint64_t _id) 
        : win_id(_id) {}


};


// ============================================================================
// Struct: keyless_window_group_select_1_struct_out
// ============================================================================
struct keyless_window_group_select_1_struct_out {
    int64_t conteggio;


};


#endif // KEYLESS_WINDOW_GROUP_STRUCTS_HPP