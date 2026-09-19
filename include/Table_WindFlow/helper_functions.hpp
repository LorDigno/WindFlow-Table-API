#ifndef HELPER_FUNCTIONS_HPP
#define HELPER_FUNCTIONS_HPP

#include <chrono>
#include <cstdint>
#include <string>

//funzioni helper per il parsing dei tipi elementari
inline std::string parse_STRING(const std::string& s) { return s; }
inline int32_t     parse_INT(const std::string& s)    { return std::stoi(s); }
inline int64_t     parse_BIGINT(const std::string& s) { return std::stoll(s); }
inline float       parse_FLOAT(const std::string& s)  { return std::stof(s); }
inline double      parse_DOUBLE(const std::string& s) { return std::stod(s); }
inline bool        parse_BOOLEAN(const std::string& s){ return s == "1" || s == "true" || s == "TRUE"; }

// Converte 'YYYY-MM-DDTHH:MM:SS.mmmZ' in microsecondi da Unix Epoch (1970-01-01 00:00:00 UTC)
inline uint64_t parse_ISO8601(const std::string& s) {
    if (s.size() < 23) return 0;

    // 1. Parsing componenti data
    int64_t year  = (s[0] - '0') * 1000 + (s[1] - '0') * 100 + (s[2] - '0') * 10 + (s[3] - '0');
    unsigned month = (s[5] - '0') * 10 + (s[6] - '0');
    unsigned day   = (s[8] - '0') * 10 + (s[9] - '0');

    // 2. Parsing componenti orarie
    uint64_t hours = (s[11] - '0') * 10 + (s[12] - '0');
    uint64_t mins  = (s[14] - '0') * 10 + (s[15] - '0');
    uint64_t secs  = (s[17] - '0') * 10 + (s[18] - '0');
    uint64_t ms    = (s[20] - '0') * 100 + (s[21] - '0') * 10 + (s[22] - '0');

    // 3. Algoritmo O(1) di conteggio giorni rispetto a 1970-01-01 (algoritmo civile di Hinnant)
    year -= (month <= 2);
    const int64_t era = (year >= 0 ? year : year - 399) / 400;
    const unsigned yoe = static_cast<unsigned>(year - era * 400);
    const unsigned doy = (153 * (month > 2 ? month - 3 : month + 9) + 2) / 5 + day - 1;
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    int64_t total_days = era * 146097 + static_cast<int64_t>(doe) - 719468;

    if (total_days < 0) return 0; // Guardia per date antecedenti al 1970

    // 4. Conversione finale continua in microsecondi
    uint64_t total_secs = static_cast<uint64_t>(total_days) * 86400ULL + hours * 3600ULL + mins * 60ULL + secs;
    return (total_secs * 1000ULL + ms) * 1000ULL;
}

// Converte microsecondi da Unix Epoch (1970-01-01 00:00:00 UTC) nella stringa 'YYYY-MM-DDTHH:MM:SS.mmmZ'
inline std::string reformat_ISO8601(uint64_t ts_us) {
    uint64_t total_secs = ts_us / 1000000ULL;
    uint32_t ms = static_cast<uint32_t>((ts_us % 1000000ULL) / 1000ULL);

    int64_t total_days = static_cast<int64_t>(total_secs / 86400ULL);
    uint32_t day_secs   = static_cast<uint32_t>(total_secs % 86400ULL);

    uint32_t hours = day_secs / 3600;
    uint32_t mins  = (day_secs % 3600) / 60;
    uint32_t secs  = day_secs % 60;

    // Algoritmo civile inverso di Hinnant (O(1), senza tabelle né salti)
    int64_t z = total_days + 719468;
    int64_t era = (z >= 0 ? z : z - 146096) / 146097;
    unsigned doe = static_cast<unsigned>(z - era * 146097);
    unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    int64_t y = static_cast<int64_t>(yoe) + era * 400;
    unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    unsigned mp = (5 * doy + 2) / 153;
    unsigned d = doy - (153 * mp + 2) / 5 + 1;
    unsigned m = mp < 10 ? mp + 3 : mp - 9;
    y += (m <= 2);

    // Scrittura diretta su stringa preallocata di 24 caratteri
    std::string out(24, ' ');

    // YYYY
    out[0] = '0' + static_cast<char>((y / 1000) % 10);
    out[1] = '0' + static_cast<char>((y / 100) % 10);
    out[2] = '0' + static_cast<char>((y / 10) % 10);
    out[3] = '0' + static_cast<char>(y % 10);
    out[4] = '-';

    // MM
    out[5] = '0' + static_cast<char>(m / 10);
    out[6] = '0' + static_cast<char>(m % 10);
    out[7] = '-';

    // DD
    out[8] = '0' + static_cast<char>(d / 10);
    out[9] = '0' + static_cast<char>(d % 10);
    out[10] = 'T';

    // HH
    out[11] = '0' + static_cast<char>(hours / 10);
    out[12] = '0' + static_cast<char>(hours % 10);
    out[13] = ':';

    // MM
    out[14] = '0' + static_cast<char>(mins / 10);
    out[15] = '0' + static_cast<char>(mins % 10);
    out[16] = ':';

    // SS
    out[17] = '0' + static_cast<char>(secs / 10);
    out[18] = '0' + static_cast<char>(secs % 10);
    out[19] = '.';

    // mmm (millisecondi su 3 cifre con padding a zero)
    out[20] = '0' + static_cast<char>((ms / 100) % 10);
    out[21] = '0' + static_cast<char>((ms / 10) % 10);
    out[22] = '0' + static_cast<char>(ms % 10);
    out[23] = 'Z';

    return out;
}

// Restituisce i microsecondi correnti da Unix Epoch (1970-01-01 00:00:00 UTC)
inline uint64_t current_time_micros() {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()
    );
}

#endif