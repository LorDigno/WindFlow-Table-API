#ifndef Q1_Q2_JOIN_STRUCTS_HPP
#define Q1_Q2_JOIN_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: q1_q2_join_output
// ============================================================================
struct q1_q2_join_output {
    std::string sensor_id;
    double temperature;
    double humidity;


    bool operator==(const q1_q2_join_output& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output> {
        size_t operator()(const q1_q2_join_output& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_2
// ============================================================================
struct q1_q2_join_output_2 {
    std::string sensor_id;
    double AVG_temperature;
    int64_t COUNT_;
    double SUM_temperature;


    bool operator==(const q1_q2_join_output_2& other) const {
        return sensor_id == other.sensor_id && AVG_temperature == other.AVG_temperature && COUNT_ == other.COUNT_ && SUM_temperature == other.SUM_temperature;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_2> {
        size_t operator()(const q1_q2_join_output_2& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.AVG_temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.COUNT_) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.SUM_temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_3
// ============================================================================
struct q1_q2_join_output_3 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;


    bool operator==(const q1_q2_join_output_3& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && conteggio == other.conteggio;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_3> {
        size_t operator()(const q1_q2_join_output_3& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.avg_temp) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.conteggio) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_4
// ============================================================================
struct q1_q2_join_output_4 {
    std::string sensor_id;
    double humidity;


    bool operator==(const q1_q2_join_output_4& other) const {
        return sensor_id == other.sensor_id && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_4> {
        size_t operator()(const q1_q2_join_output_4& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_5
// ============================================================================
struct q1_q2_join_output_5 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;
    double humidity;


    bool operator==(const q1_q2_join_output_5& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && conteggio == other.conteggio && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_5> {
        size_t operator()(const q1_q2_join_output_5& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.avg_temp) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.conteggio) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_6
// ============================================================================
struct q1_q2_join_output_6 {
    std::string sensor_id;
    double avg_temp;
    double humidity;


    bool operator==(const q1_q2_join_output_6& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && humidity == other.humidity;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_6> {
        size_t operator()(const q1_q2_join_output_6& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.avg_temp) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // Q1_Q2_JOIN_STRUCTS_HPP