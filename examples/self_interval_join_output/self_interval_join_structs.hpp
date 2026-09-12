#ifndef SELF_INTERVAL_JOIN_STRUCTS_HPP
#define SELF_INTERVAL_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_self_interval_join_from_3
// ============================================================================
struct source_self_interval_join_from_3 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: renaming_for_selfjoin_select_4_struct_out
// ============================================================================
struct renaming_for_selfjoin_select_4_struct_out {
    std::string sensor_id;
    double temp;
    double hum;


};


// ============================================================================
// Struct: source_self_interval_join_from_3_unified_renaming_for_selfjoin_select_4_struct_out
// ============================================================================
struct source_self_interval_join_from_3_unified_renaming_for_selfjoin_select_4_struct_out {
    std::string sensor_id;
    double temperature;
    double humidity;
    double temp;
    double hum;


};


// ============================================================================
// Struct: self_interval_join_join_interval_2_key_struct
// ============================================================================
struct self_interval_join_join_interval_2_key_struct {
    std::string sensor_id;


    bool operator==(const self_interval_join_join_interval_2_key_struct& other) const {
        return sensor_id == other.sensor_id;
    }
};

namespace std {
    template<>
    struct hash<self_interval_join_join_interval_2_key_struct> {
        size_t operator()(const self_interval_join_join_interval_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: self_interval_join_select_1_struct_out
// ============================================================================
struct self_interval_join_select_1_struct_out {
    std::string sensor_id;
    double temperature;
    double hum;


};


#endif // SELF_INTERVAL_JOIN_STRUCTS_HPP