#ifndef MULTIPLE_JOIN_STRUCTS_HPP
#define MULTIPLE_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_multiple_join_from_3
// ============================================================================
struct source_multiple_join_from_3 {
    std::string sensor_id;
    double temp;
    double hum;


};


// ============================================================================
// Struct: source_multiple_join_from_4
// ============================================================================
struct source_multiple_join_from_4 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: source_multiple_join_from_3_unified_source_multiple_join_from_4
// ============================================================================
struct source_multiple_join_from_3_unified_source_multiple_join_from_4 {
    std::string sensor_id;
    double temp;
    double hum;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: multiple_join_join_window_2_key_struct
// ============================================================================
struct multiple_join_join_window_2_key_struct {
    std::string sensor_id;


    bool operator==(const multiple_join_join_window_2_key_struct& other) const {
        return sensor_id == other.sensor_id;
    }
};

namespace std {
    template<>
    struct hash<multiple_join_join_window_2_key_struct> {
        size_t operator()(const multiple_join_join_window_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // MULTIPLE_JOIN_STRUCTS_HPP