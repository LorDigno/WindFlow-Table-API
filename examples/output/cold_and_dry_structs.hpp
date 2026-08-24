#ifndef COLD_AND_DRY_STRUCTS_HPP
#define COLD_AND_DRY_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: sensor_input
// ============================================================================
struct sensor_input {
    std::string sensor_id;
    double temperature;
    double humidity;


    bool operator==(const sensor_input& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<sensor_input> {
        size_t operator()(const sensor_input& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // COLD_AND_DRY_STRUCTS_HPP