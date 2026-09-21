#ifndef AVG_SELLING_PRICE_BY_SELLER_STRUCTS_HPP
#define AVG_SELLING_PRICE_BY_SELLER_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_winning_price_per_auction_by_seller_from_6
// ============================================================================
struct source_winning_price_per_auction_by_seller_from_6 {
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
// Struct: source_winning_price_per_auction_by_seller_from_7
// ============================================================================
struct source_winning_price_per_auction_by_seller_from_7 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7
// ============================================================================
struct source_winning_price_per_auction_by_seller_from_6_unified_source_winning_price_per_auction_by_seller_from_7 {
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
// Struct: winning_price_per_auction_by_seller_join_interval_5_key_struct
// ============================================================================
struct winning_price_per_auction_by_seller_join_interval_5_key_struct {
    int64_t auction_id;


    bool operator==(const winning_price_per_auction_by_seller_join_interval_5_key_struct& other) const {
        return auction_id == other.auction_id;
    }
};

namespace std {
    template<>
    struct hash<winning_price_per_auction_by_seller_join_interval_5_key_struct> {
        size_t operator()(const winning_price_per_auction_by_seller_join_interval_5_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.auction_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: winning_price_per_auction_by_seller_window_group_by_4_key_struct
// ============================================================================
struct winning_price_per_auction_by_seller_window_group_by_4_key_struct {
    int64_t auction_id;
    int64_t seller;


    bool operator==(const winning_price_per_auction_by_seller_window_group_by_4_key_struct& other) const {
        return auction_id == other.auction_id && seller == other.seller;
    }
};

namespace std {
    template<>
    struct hash<winning_price_per_auction_by_seller_window_group_by_4_key_struct> {
        size_t operator()(const winning_price_per_auction_by_seller_window_group_by_4_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.auction_id) + 0x9e3779b9 + (h << 6) + (h >> 2);
            h ^= std::hash<int64_t>{}(k.seller) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: winning_price_per_auction_by_seller_window_group_by_4_struct_out
// ============================================================================
struct winning_price_per_auction_by_seller_window_group_by_4_struct_out {
    int64_t auction_id;
    int64_t seller;
    int64_t MAX_price = std::numeric_limits<int64_t>::lowest(); 
    uint64_t win_id = 0; 

    winning_price_per_auction_by_seller_window_group_by_4_struct_out() = default;

    winning_price_per_auction_by_seller_window_group_by_4_struct_out(uint64_t _id) 
        : win_id(_id) {}

    winning_price_per_auction_by_seller_window_group_by_4_struct_out(const winning_price_per_auction_by_seller_window_group_by_4_key_struct& _key, uint64_t _id) 
        : auction_id(_key.auction_id), seller(_key.seller), win_id(_id) {}

};


// ============================================================================
// Struct: winning_price_per_auction_by_seller_select_3_struct_out
// ============================================================================
struct winning_price_per_auction_by_seller_select_3_struct_out {
    int64_t seller;
    int64_t final;


};


// ============================================================================
// Struct: avg_selling_price_by_seller_global_group_by_2_key_struct
// ============================================================================
struct avg_selling_price_by_seller_global_group_by_2_key_struct {
    int64_t seller;


    bool operator==(const avg_selling_price_by_seller_global_group_by_2_key_struct& other) const {
        return seller == other.seller;
    }
};

namespace std {
    template<>
    struct hash<avg_selling_price_by_seller_global_group_by_2_key_struct> {
        size_t operator()(const avg_selling_price_by_seller_global_group_by_2_key_struct& k) const {
            size_t h = 0;
            h ^= std::hash<int64_t>{}(k.seller) + 0x9e3779b9 + (h << 6) + (h >> 2);
            return h;
        }
    };
}

// ============================================================================
// Struct: avg_selling_price_by_seller_global_group_by_2_struct_out
// ============================================================================
struct avg_selling_price_by_seller_global_group_by_2_struct_out {
    int64_t seller;
    int64_t COUNT = 0; 
    int64_t SUM_final = 0; 
    double AVG_final = 0.0; 


};


// ============================================================================
// Struct: avg_selling_price_by_seller_select_1_struct_out
// ============================================================================
struct avg_selling_price_by_seller_select_1_struct_out {
    int64_t seller;
    double AVG_final;


};


#endif // AVG_SELLING_PRICE_BY_SELLER_STRUCTS_HPP