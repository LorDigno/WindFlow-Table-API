#ifndef INTERSECT_TESTS_STRUCTS_HPP
#define INTERSECT_TESTS_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_sensor_source_query_5_from_5
// ============================================================================
struct source_sensor_source_query_5_from_5 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: sensor_source_query_5_select_3_struct_out
// ============================================================================
struct sensor_source_query_5_select_3_struct_out {
    std::string sensor_id;
    double temperature;


    bool operator==(const sensor_source_query_5_select_3_struct_out& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature;
    }
};

namespace std {
    template<>
    struct hash<sensor_source_query_5_select_3_struct_out> {
        size_t operator()(const sensor_source_query_5_select_3_struct_out& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // INTERSECT_TESTS_STRUCTS_HPP