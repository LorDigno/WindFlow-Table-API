#ifndef DOL_TO_EUR_STRUCTS_HPP
#define DOL_TO_EUR_STRUCTS_HPP

#include <string>
#include <cstdint>
#include <functional>
#include <limits>

// ============================================================================
// Struct: source_dol_to_eur_from_2
// ============================================================================
struct source_dol_to_eur_from_2 {
    int64_t auction_id;
    int64_t bidder;
    int64_t price;
    std::string channel;
    std::string url;
    uint64_t bid_dateTime;
    std::string extra;


};


// ============================================================================
// Struct: dol_to_eur_select_1_struct_out
// ============================================================================
struct dol_to_eur_select_1_struct_out {
    int64_t auction_id;
    double price_eur;
    int64_t bidder;
    uint64_t bid_dateTime;


};


#endif // DOL_TO_EUR_STRUCTS_HPP