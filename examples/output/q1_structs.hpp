#ifndef Q1_STRUCTS_HPP
#define Q1_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>

// ============================================================================
// Struct: SensorData
// ============================================================================
struct SensorData {
    std::string sensor_id;
    double temperature;

    bool operator==(const SensorData& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature;
    }
};

namespace std {
    template<>
    struct hash<SensorData> {
        size_t operator()(const SensorData& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // Q1_STRUCTS_HPP