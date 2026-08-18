#ifndef Q1_Q2_JOIN_STRUCTS_HPP
#define Q1_Q2_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>

// ============================================================================
// Struct: q1_q2_join_output
// ============================================================================
struct q1_q2_join_output {
    std::string sensor_id;
    double temperature;
    double humidity;

};


// ============================================================================
// Struct: q1_q2_join_output_2
// ============================================================================
struct q1_q2_join_output_2 {
    std::string sensor_id;
    double AVG_temperature;
    int64_t COUNT_;
    double SUM_temperature;

};


// ============================================================================
// Struct: q1_q2_join_output_3
// ============================================================================
struct q1_q2_join_output_3 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;

};


// ============================================================================
// Struct: q1_q2_join_output_4
// ============================================================================
struct q1_q2_join_output_4 {
    std::string sensor_id;
    double humidity;

};


// ============================================================================
// Struct: q1_q2_join_output_5
// ============================================================================
struct q1_q2_join_output_5 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;
    double humidity;

};


// ============================================================================
// Struct: q1_q2_join_output_6
// ============================================================================
struct q1_q2_join_output_6 {
    std::string sensor_id;
    double avg_temp;
    double humidity;

};


#endif // Q1_Q2_JOIN_STRUCTS_HPP