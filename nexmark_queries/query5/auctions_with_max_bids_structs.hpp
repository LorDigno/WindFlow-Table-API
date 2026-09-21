#ifndef AUCTIONS_WITH_MAX_BIDS_STRUCTS_HPP
#define AUCTIONS_WITH_MAX_BIDS_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_bids_counter_per_auction_from_5
// ============================================================================
struct source_bids_counter_per_auction_from_5 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: bids_counter_per_auction_window_group_by_4_key_struct
// ============================================================================
struct bids_counter_per_auction_window_group_by_4_key_struct {
    int64_t auction_id;


    bool operator==(const bids_counter_per_auction_window_group_by_4_key_struct& other) const {
        return auction_id == other.auction_id;
    }
};

namespace std {
    template<>
    struct hash<bids_counter_per_auction_window_group_by_4_key_struct> {
        size_t operator()(const bids_counter_per_auction_window_group_by_4_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.auction_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: bids_counter_per_auction_window_group_by_4_struct_out
// ============================================================================
struct bids_counter_per_auction_window_group_by_4_struct_out {
    int64_t auction_id;
    int64_t COUNT = 0; 
    uint64_t win_id = 0; 

    bids_counter_per_auction_window_group_by_4_struct_out() = default;

    bids_counter_per_auction_window_group_by_4_struct_out(uint64_t _id) 
        : win_id(_id) {}

    bids_counter_per_auction_window_group_by_4_struct_out(const bids_counter_per_auction_window_group_by_4_key_struct& _key, uint64_t _id) 
        : auction_id(_key.auction_id), win_id(_id) {}

};


// ============================================================================
// Struct: bids_counter_per_auction_select_3_struct_out
// ============================================================================
struct bids_counter_per_auction_select_3_struct_out {
    int64_t auction_id;
    int64_t bids_counter;


};


// ============================================================================
// Struct: max_bid_count_window_group_by_7_struct_out
// ============================================================================
struct max_bid_count_window_group_by_7_struct_out {
    int64_t MAX_bids_counter = std::numeric_limits<int64_t>::lowest(); 
    uint64_t win_id = 0; 

    max_bid_count_window_group_by_7_struct_out() = default;

    max_bid_count_window_group_by_7_struct_out(uint64_t _id) 
        : win_id(_id) {}


};


// ============================================================================
// Struct: max_bid_count_select_6_struct_out
// ============================================================================
struct max_bid_count_select_6_struct_out {
    int64_t bids_counter;


    bool operator==(const max_bid_count_select_6_struct_out& other) const {
        return bids_counter == other.bids_counter;
    }
};

namespace std {
    template<>
    struct hash<max_bid_count_select_6_struct_out> {
        size_t operator()(const max_bid_count_select_6_struct_out& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.bids_counter) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

#endif // AUCTIONS_WITH_MAX_BIDS_STRUCTS_HPP