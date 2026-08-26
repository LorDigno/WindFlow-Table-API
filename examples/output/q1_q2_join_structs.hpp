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
    uint64_t win_id = 0; 

    q1_q2_join_output() = default;

    q1_q2_join_output(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output& other) const {
        return sensor_id == other.sensor_id && temperature == other.temperature && humidity == other.humidity && win_id == other.win_id;
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
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_input
// ============================================================================
struct q1_q2_join_input {
    std::string sensor_id;
    double temperature;
    double humidity;


};


// ============================================================================
// Struct: q1_q2_join_output_3
// ============================================================================
struct q1_q2_join_output_3 {
    std::string sensor_id;
    int64_t COUNT_;
    double SUM_temperature;
    double AVG_temperature;
    uint64_t win_id = 0; 

    q1_q2_join_output_3() = default;

    q1_q2_join_output_3(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output_3& other) const {
        return sensor_id == other.sensor_id && COUNT_ == other.COUNT_ && SUM_temperature == other.SUM_temperature && AVG_temperature == other.AVG_temperature && win_id == other.win_id;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_3> {
        size_t operator()(const q1_q2_join_output_3& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.COUNT_) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.SUM_temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.AVG_temperature) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_input_4
// ============================================================================
struct q1_q2_join_input_4 {
    std::string sensor_id;
    int64_t COUNT_;
    double SUM_temperature;
    double AVG_temperature;


};


// ============================================================================
// Struct: q1_q2_join_output_5
// ============================================================================
struct q1_q2_join_output_5 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;
    uint64_t win_id = 0; 

    q1_q2_join_output_5() = default;

    q1_q2_join_output_5(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output_5& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && conteggio == other.conteggio && win_id == other.win_id;
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
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_output_6
// ============================================================================
struct q1_q2_join_output_6 {
    std::string sensor_id;
    double humidity;
    uint64_t win_id = 0; 

    q1_q2_join_output_6() = default;

    q1_q2_join_output_6(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output_6& other) const {
        return sensor_id == other.sensor_id && humidity == other.humidity && win_id == other.win_id;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_6> {
        size_t operator()(const q1_q2_join_output_6& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_input_7
// ============================================================================
struct q1_q2_join_input_7 {
    std::string sensor_id;
    double humidity;


};


// ============================================================================
// Struct: q1_q2_join_output_8
// ============================================================================
struct q1_q2_join_output_8 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;
    double humidity;
    uint64_t win_id = 0; 

    q1_q2_join_output_8() = default;

    q1_q2_join_output_8(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output_8& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && conteggio == other.conteggio && humidity == other.humidity && win_id == other.win_id;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_8> {
        size_t operator()(const q1_q2_join_output_8& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.avg_temp) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.conteggio) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: q1_q2_join_input_9
// ============================================================================
struct q1_q2_join_input_9 {
    std::string sensor_id;
    double avg_temp;
    int64_t conteggio;
    double humidity;


};


// ============================================================================
// Struct: q1_q2_join_output_10
// ============================================================================
struct q1_q2_join_output_10 {
    std::string sensor_id;
    double avg_temp;
    double humidity;
    uint64_t win_id = 0; 

    q1_q2_join_output_10() = default;

    q1_q2_join_output_10(uint64_t _id) 
        : win_id(_id) {}


    bool operator==(const q1_q2_join_output_10& other) const {
        return sensor_id == other.sensor_id && avg_temp == other.avg_temp && humidity == other.humidity && win_id == other.win_id;
    }
};

namespace std {
    template<>
    struct hash<q1_q2_join_output_10> {
        size_t operator()(const q1_q2_join_output_10& k) const {
            size_t h = 0;
            h ^= std::hash<std::string>{}(k.sensor_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.avg_temp) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<double>{}(k.humidity) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<uint64_t>{}(k.win_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // Q1_Q2_JOIN_STRUCTS_HPP