#ifndef AVG_COLD_TEMPERATURE_STRUCTS_HPP
#define AVG_COLD_TEMPERATURE_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: avg_cold_temperature
// ============================================================================
struct avg_cold_temperature {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: avg_cold_temperature_2
// ============================================================================
struct avg_cold_temperature_2 {
    std::string sensor_id;
    int64_t COUNT_;
    double SUM_temperature;
    double AVG_temperature;


};


// ============================================================================
// Struct: avg_cold_temperature_3
// ============================================================================
struct avg_cold_temperature_3 {
    std::string sensor_id;
    double avg_temp;


};


#endif // AVG_COLD_TEMPERATURE_STRUCTS_HPP