#ifndef AUCTION_EXPANDED_STRUCTS_HPP
#define AUCTION_EXPANDED_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_auction_expanded_from_4
// ============================================================================
struct source_auction_expanded_from_4 {
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
// Struct: source_auction_expanded_from_5
// ============================================================================
struct source_auction_expanded_from_5 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: source_auction_expanded_from_4_unified_source_auction_expanded_from_5
// ============================================================================
struct source_auction_expanded_from_4_unified_source_auction_expanded_from_5 {
    int64_t auction_id;
    std::string item_name;
    std::string description;
    int64_t initial_bid;
    int64_t reserve;
    uint64_t auction_dateTime;
    uint64_t expires;
    int64_t seller;
    int64_t category;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: auction_expanded_join_interval_2_key_struct
// ============================================================================
struct auction_expanded_join_interval_2_key_struct {
    int64_t auction_id;


    bool operator==(const auction_expanded_join_interval_2_key_struct& other) const {
        return auction_id == other.auction_id;
    }
};

namespace std {
    template<>
    struct hash<auction_expanded_join_interval_2_key_struct> {
        size_t operator()(const auction_expanded_join_interval_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.auction_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // AUCTION_EXPANDED_STRUCTS_HPP