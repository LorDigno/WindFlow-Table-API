#ifndef SPECIFIC_ID_STRUCTS_HPP
#define SPECIFIC_ID_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_specific_id_from_3
// ============================================================================
struct source_specific_id_from_3 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: specific_id_select_1_struct_out
// ============================================================================
struct specific_id_select_1_struct_out {
    int64_t auction_id;
    int64_t price;


};


#endif // SPECIFIC_ID_STRUCTS_HPP