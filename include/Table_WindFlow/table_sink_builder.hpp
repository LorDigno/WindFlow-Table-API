#ifndef TABLE_SINK_BUILDER_HPP
#define TABLE_SINK_BUILDER_HPP

#include <string>
#include <fstream>
#include <iostream>
#include <memory>
#include <functional>
#include <optional>
#include <windflow.hpp>

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

//funtore per scrittura di flusso su file csv
template <typename TupleT>
class Sink_Functor {
    public:
        //riceve la tupla e scrive direttamente sullo stream
        using FormatterFn = std::function<void(const TupleT&, std::ostream&)>;

    private:
        FormatterFn formatter_lambda;
        std::string header;
        int parallelism;

        //gestione del file del sink
        std::string filename;;
        std::shared_ptr<std::ofstream> out_file;
        std::string actual_filename;
        bool is_initialized = false;

        //inizializza lo stream di lettura del file di output
        void init_file(size_t replica_id) {
            if (is_initialized) return;
            is_initialized = true;

            actual_filename = filename + "_output";
            if (parallelism > 1) {
                actual_filename += std::to_string(replica_id);
            } 
            actual_filename += ".csv";

            out_file = std::make_shared<std::ofstream>(actual_filename);
            if (!out_file->is_open()) {
                std::cerr << "[ERROR] Impossibile creare/aprire il file sink: " << actual_filename << std::endl;
                return;
            }

            std::cout << "[SINK] File " << actual_filename << " aperto." << std::endl;

            if (!header.empty()) {
                *out_file << header << "\n";
            }
        }

    public:
        Sink_Functor(
            const std::string& path,
            FormatterFn formatter,
            const std::string& csv_header = "",
            int par = 1
        ) : filename(path),
            formatter_lambda(formatter),
            header(csv_header),
            parallelism(par) {}

        void operator()(std::optional<TupleT>& input, wf::RuntimeContext& ctx) {
            //inizializzo il file alla prima tupla
            if(!is_initialized){
                init_file(ctx.getReplicaIndex());
            }

            //fine dello stream
            if (!input) {
                if (out_file && out_file->is_open()) {
                    out_file->flush();
                    out_file->close();
                }
                std::cout << "[SINK" << ctx.getReplicaIndex() << "] File " << actual_filename << " completato e chiuso." << std::endl;
                return;
            }

            //scrittura sul file
            if (out_file && out_file->is_open()) {
                formatter_lambda(*input, *out_file);
                *out_file << "\n";
            }
        }
};

template <typename TupleT>
class Table_Sink_Builder {
    public:
        using FormatterFn = std::function<void(const TupleT&, std::ostream&)>;

    private:
        std::string filename;
        FormatterFn formatter_lambda;
        std::string header = "";
        std::string op_name = "TableSink_Operator";
        size_t parallelism = 1;

    public:
        Table_Sink_Builder(const std::string& path, FormatterFn formatter)
            : filename(path), formatter_lambda(formatter) {}

        Table_Sink_Builder& withName(const std::string& name) {
            this->op_name = name;
            return *this;
        }

        Table_Sink_Builder& withHeader(const std::string& csv_header) {
            this->header = csv_header;
            return *this;
        }

        Table_Sink_Builder& withParallelism(size_t par) {
            this->parallelism = par;
            return *this;
        }

        auto build() {
            Sink_Functor<TupleT> functor(filename, formatter_lambda, header, parallelism);

            return wf::Sink_Builder(functor)
                .withName(op_name)
                .withParallelism(parallelism)
                .build();
        }
};

#endif // TABLE_SINK_BUILDER_HPP