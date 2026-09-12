#ifndef UNARY_SIMPLE_TEST_STRUCTS_HPP
#define UNARY_SIMPLE_TEST_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_unary_simple_test_from_5
// ============================================================================
struct source_unary_simple_test_from_5 {
    std::string sensor_id;
    double temperature;
    double humidity;


    bool operator==(const source_unary_simple_test_from_5& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<source_unary_simple_test_from_5> {
        size_t operator()(const source_unary_simple_test_from_5& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: unary_simple_test_global_group_by_2_key_struct
// ============================================================================
struct unary_simple_test_global_group_by_2_key_struct {
    std::string sensor_id;


    bool operator==(const unary_simple_test_global_group_by_2_key_struct& other) const {
        return sensor_id == other.sensor_id;
    }
};

namespace std {
    template<>
    struct hash<unary_simple_test_global_group_by_2_key_struct> {
        size_t operator()(const unary_simple_test_global_group_by_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: unary_simple_test_global_group_by_2_struct_out
// ============================================================================
struct unary_simple_test_global_group_by_2_struct_out {
    std::string sensor_id;
    int64_t COUNT = 0; 


};


// ============================================================================
// Struct: unary_simple_test_select_1_struct_out
// ============================================================================
struct unary_simple_test_select_1_struct_out {
    std::string sensor_id;
    int64_t conteggio;


};


#endif // UNARY_SIMPLE_TEST_STRUCTS_HPP