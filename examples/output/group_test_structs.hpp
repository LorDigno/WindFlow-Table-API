#ifndef GROUP_TEST_STRUCTS_HPP
#define GROUP_TEST_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: Sensor_Input
// ============================================================================
struct Sensor_Input {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: Sensor_Key
// ============================================================================
struct Sensor_Key {
    std::string sensor_id;


    bool operator==(const Sensor_Key& other) const {
        return sensor_id == other.sensor_id;
    }
};

namespace std {
    template<>
    struct hash<Sensor_Key> {
        size_t operator()(const Sensor_Key& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: Grouped_Sensors
// ============================================================================
struct Grouped_Sensors {
    std::string sensor_id;
    double SUM_temperature = 0.0; 
    double MAX_humidity = std::numeric_limits<double>::lowest(); 
    uint64_t win_id = 0; 

    Grouped_Sensors() = default;

    Grouped_Sensors(uint64_t _id) 
        : win_id(_id) {}

    Grouped_Sensors(const Sensor_Key& _key, uint64_t _id) 
        : sensor_id(_key.sensor_id), win_id(_id) {}

};


#endif // GROUP_TEST_STRUCTS_HPP