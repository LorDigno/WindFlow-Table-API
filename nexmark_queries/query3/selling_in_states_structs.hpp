#ifndef SELLING_IN_STATES_STRUCTS_HPP
#define SELLING_IN_STATES_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_selling_in_states_from_4
// ============================================================================
struct source_selling_in_states_from_4 {
    int64_t person_id;
    std::string name;
    std::string email_address;
    std::string credit_card;
    std::string city;
    std::string state;
    uint64_t person_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: source_auction_source_query_4_from_7
// ============================================================================
struct source_auction_source_query_4_from_7 {
    int64_t auction_id;
    std::string item_name;
    std::string description;
    int64_t initial_bid;
    int64_t reserve;
    uint64_t auction_dateTime;
    uint64_t expires;
    int64_t seller;
    int64_t category;


};


// ============================================================================
// Struct: auction_source_query_4_select_5_struct_out
// ============================================================================
struct auction_source_query_4_select_5_struct_out {
    int64_t auction_id;
    std::string item_name;
    std::string description;
    int64_t initial_bid;
    int64_t reserve;
    uint64_t auction_dateTime;
    uint64_t expires;
    int64_t person_id;
    int64_t category;


};


// ============================================================================
// Struct: source_selling_in_states_from_4_unified_auction_source_query_4_select_5_struct_out
// ============================================================================
struct source_selling_in_states_from_4_unified_auction_source_query_4_select_5_struct_out {
    int64_t person_id;
    std::string name;
    std::string email_address;
    std::string credit_card;
    std::string city;
    std::string state;
    uint64_t person_dateTime;
    std::string extra;
    int64_t auction_id;
    std::string item_name;
    std::string description;
    int64_t initial_bid;
    int64_t reserve;
    uint64_t auction_dateTime;
    uint64_t expires;
    int64_t category;


};


// ============================================================================
// Struct: selling_in_states_join_interval_2_key_struct
// ============================================================================
struct selling_in_states_join_interval_2_key_struct {
    int64_t person_id;


    bool operator==(const selling_in_states_join_interval_2_key_struct& other) const {
        return person_id == other.person_id;
    }
};

namespace std {
    template<>
    struct hash<selling_in_states_join_interval_2_key_struct> {
        size_t operator()(const selling_in_states_join_interval_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.person_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: selling_in_states_select_1_struct_out
// ============================================================================
struct selling_in_states_select_1_struct_out {
    std::string name;
    std::string city;
    std::string state;
    int64_t auction_id;


};


#endif // SELLING_IN_STATES_STRUCTS_HPP