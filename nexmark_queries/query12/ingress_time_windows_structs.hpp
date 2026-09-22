#ifndef INGRESS_TIME_WINDOWS_STRUCTS_HPP
#define INGRESS_TIME_WINDOWS_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_ingress_time_windows_from_3
// ============================================================================
struct source_ingress_time_windows_from_3 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: ingress_time_windows_window_group_by_2_key_struct
// ============================================================================
struct ingress_time_windows_window_group_by_2_key_struct {
    int64_t bidder;


    bool operator==(const ingress_time_windows_window_group_by_2_key_struct& other) const {
        return bidder == other.bidder;
    }
};

namespace std {
    template<>
    struct hash<ingress_time_windows_window_group_by_2_key_struct> {
        size_t operator()(const ingress_time_windows_window_group_by_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.bidder) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: ingress_time_windows_window_group_by_2_struct_out
// ============================================================================
struct ingress_time_windows_window_group_by_2_struct_out {
    int64_t bidder;
    int64_t COUNT = 0; 
    uint64_t win_id = 0; 

    ingress_time_windows_window_group_by_2_struct_out() = default;

    ingress_time_windows_window_group_by_2_struct_out(uint64_t _id) 
        : win_id(_id) {}

    ingress_time_windows_window_group_by_2_struct_out(const ingress_time_windows_window_group_by_2_key_struct& _key, uint64_t _id) 
        : bidder(_key.bidder), win_id(_id) {}

};


// ============================================================================
// Struct: ingress_time_windows_select_1_struct_out
// ============================================================================
struct ingress_time_windows_select_1_struct_out {
    int64_t bidder;
    int64_t processed;


};


#endif // INGRESS_TIME_WINDOWS_STRUCTS_HPP