#ifndef SUM_OF_BINARY_STRUCTS_HPP
#define SUM_OF_BINARY_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_sum_of_binary_from_4
// ============================================================================
struct source_sum_of_binary_from_4 {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: sum_of_binary_global_group_by_2_key_struct
// ============================================================================
struct sum_of_binary_global_group_by_2_key_struct {
    std::string sensor_id;


    bool operator==(const sum_of_binary_global_group_by_2_key_struct& other) const {
        return sensor_id == other.sensor_id;
    }
};

namespace std {
    template<>
    struct hash<sum_of_binary_global_group_by_2_key_struct> {
        size_t operator()(const sum_of_binary_global_group_by_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: sum_of_binary_global_group_by_2_struct_out
// ============================================================================
struct sum_of_binary_global_group_by_2_struct_out {
    std::string sensor_id;
    double SUM_temperature_+_humidity = 0.0; 


};


#endif // SUM_OF_BINARY_STRUCTS_HPP