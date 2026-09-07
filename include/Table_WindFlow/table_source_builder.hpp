#ifndef TABLE_SOURCE_BUILDER_HPP
#define TABLE_SOURCE_BUILDER_HPP

#include <string>
#include <sstream>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <vector>
#include <unordered_map>
#include <filesystem> 
#include <cassert> 
#include <functional>
#include <windflow.hpp>

//struct che rappresenta uno split
struct File_Split{
    uint64_t offset = 0;
    uint64_t length = 0; 
};

//funzioni helper per il parsing dei tipi elementari
inline std::string parse_STRING(const std::string& s) { return s; }
inline int32_t     parse_INT(const std::string& s)    { return std::stoi(s); }
inline int64_t     parse_BIGINT(const std::string& s) { return std::stoll(s); }
inline float       parse_FLOAT(const std::string& s)  { return std::stof(s); }
inline double      parse_DOUBLE(const std::string& s) { return std::stod(s); }
inline bool        parse_BOOLEAN(const std::string& s){ return s == "1" || s == "true" || s == "TRUE"; }

//funzioni helper per il parsing del formato temporale
// Converte 'YYYY-MM-DDTHH:MM:SS.mmmZ' in microsecondi lineari continui
inline uint64_t parse_TIMESTAMP_ISO8601(const std::string& s) {
    if (s.size() < 23) return 0;

    // 1. Parsing componenti data
    uint64_t year  = (s[0] - '0') * 1000 + (s[1] - '0') * 100 + (s[2] - '0') * 10 + (s[3] - '0');
    uint64_t month = (s[5] - '0') * 10 + (s[6] - '0');
    uint64_t day   = (s[8] - '0') * 10 + (s[9] - '0');

    // 2. Parsing componenti orarie
    uint64_t hours = (s[11] - '0') * 10 + (s[12] - '0');
    uint64_t mins  = (s[14] - '0') * 10 + (s[15] - '0');
    uint64_t secs  = (s[17] - '0') * 10 + (s[18] - '0');
    uint64_t ms    = (s[20] - '0') * 100 + (s[21] - '0') * 10 + (s[22] - '0');

    // 3. Tabella giorni cumulativi pregressi per mese (anno non bisestile)
    static const uint32_t days_before_month[13] = {
        0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334
    };

    // 4. Calcolo giorni totali assoluti (conteggiando gli anni bisestili)
    uint64_t leap_years = (year - 1) / 4 - (year - 1) / 100 + (year - 1) / 400;
    uint64_t total_days = (year * 365ULL) + leap_years + days_before_month[month] + day;
    
    // Giorno bisestile per l'anno corrente dopo febbraio
    bool is_current_leap = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
    if (month > 2 && is_current_leap) {
        total_days++;
    }

    // 5. Conversione lineare continua in microsecondi
    uint64_t total_secs = total_days * 86400ULL + hours * 3600ULL + mins * 60ULL + secs;
    return (total_secs * 1000ULL + ms) * 1000ULL;
}

//funtore che implementa il ciclo di getline
template <typename TupleT>
class Source_Functor {
    //esegue il parsing della stringa e lo mette in TupleT, se c'è l'intero sarà il timestamp (microsecondi).
    using ParserFn = std::function<void(const std::string&, TupleT&, uint64_t&)>;

    private:
        std::string file_path;
        bool header_skip;

        //mappa degli split per replicaIndex
        std::unordered_map<int, std::vector<File_Split>> splits_map;

        //funzione che data una riga la parsa, passata come una lambda
        ParserFn parser_lambda;

        //flag per lo shipper
        bool event_time;

        //delay di watermarking
        uint64_t delay;
        
        //flag che sceglie il metodo di watermarking
        bool is_ordered;

        //necessari per il watermarking
        uint64_t max_ts = 0, global_first_ts = 0 , last_wm = 0;
        bool first_wm = true;

        void process_ordered(uint64_t& current_ts, uint64_t& current_wm) {
            //normalizza secondo la prima tupla
            current_ts = (current_ts >= global_first_ts) ? (current_ts - global_first_ts) : 0;
            current_wm = current_ts;
        }

        void process_out_of_order(uint64_t& current_ts, uint64_t& current_wm) {
            //normalizza secondo il delay
            current_ts = (current_ts + delay >= global_first_ts) 
                            ? (current_ts + delay - global_first_ts) 
                            : 0;

            max_ts = std::max(max_ts, current_ts);
            current_wm = (max_ts >= delay) ? (max_ts - delay) : 0;
        }

    public:
        Source_Functor(
            const std::string& path, bool head, ParserFn pars, 
            bool ev, bool order, uint64_t del, uint64_t base_ts,
            std::unordered_map<int, std::vector<File_Split>> splits
        ) 
            : file_path(path),
            header_skip(head),
            parser_lambda(pars),
            event_time(ev),
            is_ordered(order),
            delay(del),
            global_first_ts(base_ts),
            splits_map(splits) {}
    
        void operator()(wf::Source_Shipper<TupleT> &shipper, wf::RuntimeContext& ctx) {
            //replicaIndex necessario a ricavare gli split
            int replica_id = static_cast<int>(ctx.getReplicaIndex());

            //apro il file
            std::ifstream file(file_path);
            if (!file.is_open()) {
                std::cerr << "[ERROR] Impossibile aprire il file: " << file_path << std::endl;
                return;
            }

            //recupero il vector di split di questa replica
            auto it = splits_map.find(replica_id);
            if (it == splits_map.end()){
                std::cerr << "[ERROR] Split non trovato per replica:  " << replica_id << std::endl;
                return;
            } 
            const auto& my_splits = it->second;

            //ciclo di lettura degli split
            for (const auto& split : my_splits){
                //vado in posizione pari a offset
                file.clear();
                file.seekg(split.offset);
                std::string line;

                //il primo split può dover saltare l'header, altrimenti non salta righe
                if(split.offset == 0){
                    if(header_skip){             
                        std::getline(file, line);
                    }
                }else{
                    //gli altri split saltano la riga a mezzo in cui si trovano ad offset
                    std::getline(file, line);
                }

                //ciclo di lettura delle righe dello split
                std::streampos split_end = static_cast<std::streampos>(split.offset + split.length);
                while (
                    file.tellg() >= 0
                    && file.tellg() <= split_end
                    && std::getline(file, line)
                ) {
                    if (line.empty() || line.front() == '\r') continue;

                    uint64_t timestamp = 0, watermark = 0;
                    TupleT tuple;

                    parser_lambda(line, tuple, timestamp);

                    if(event_time){
                        //usa la politica corretta per la normalizzazione e il watermarking
                        if (is_ordered) {
                            process_ordered(timestamp, watermark);
                        } else {
                            process_out_of_order(timestamp, watermark);
                        }
    
                        shipper.pushWithTimestamp(tuple, timestamp);
                        if(watermark > last_wm || first_wm){
                            first_wm = false;
                            last_wm = watermark;
                            shipper.setNextWatermark(watermark);
                        }
                    }
                    else{
                        shipper.push(tuple);
                    }
                }
            }

            file.close();
        }
};

template<typename TupleT>
class Table_Source_Builder{
    //esegue il parsing della stringa e lo mette in TupleT, se c'è l'intero sarà il timestamp (microsecondi).
    using ParserFn = std::function<void(const std::string&, TupleT&, uint64_t&)>;

    private:
        //parser function
        ParserFn parser_lambda;

        //filepath da leggere
        std::string filepath;

        //attributi per il parallelismo e lo splitting
        int parallelism = 1;
        uint64_t split_size = 0;

        //se skippare l'header
        bool header = false;

        //attributi per la politica EVENT_TIME
        bool event_time = false;     
        uint64_t delay = 0;         
        bool ordered = false;    

        std::string op_name = "TableSource_Operator";

        //metodo che crea gli split di un file unico dato parallelismo e block_size voluta
        //rende una mappa replicaIndex->[splits]
        std::unordered_map<int, std::vector<File_Split>> make_splits(
            std::string filepath, int par, uint64_t split_size
        ){
            assert(par >= 1);

            std::unordered_map<int, std::vector<File_Split>> splits_per_thread;

            //inizializzo la mappa per ogni thread
            for (int i = 0; i < par; ++i) {
                splits_per_thread[i] = std::vector<File_Split>();
            }

            //leggo la dimensione del file
            uintmax_t file_size = std::filesystem::file_size(filepath);
            
            //caso a thread singolo
            if (par == 1) {
                splits_per_thread[0].push_back({0, file_size});
                return splits_per_thread;
            }
            
            //caso con split non custom, divide equamente il file
            if (split_size == 0){
                split_size = std::max<uint64_t>(1ULL, (file_size + par - 1) / par);
            }

            uint64_t offset = 0;
            int split_idx = 0;

            //ciclo di creazione degli split
            while (offset < file_size) {
                //l'ultimo split avrà una length ridotta
                uint64_t current_len = std::min(split_size, file_size - offset);
                
                //assegnazione a round robin per bilanciare il carico
                //idealmente rende anche più rapido l'avanzamento del watermark
                int assigned_thread = split_idx % par;
                splits_per_thread[assigned_thread].push_back({offset, current_len});

                //aumento i contatori
                offset += current_len;
                ++split_idx;
            }

            return splits_per_thread;
        }

    public: 
        Table_Source_Builder(const std::string& path, ParserFn parser)
            :   parser_lambda(parser), filepath(path) {}

        Table_Source_Builder& withName(const std::string& name) {
            this->op_name = name;
            return *this;
        }

        //assegna il parallelismo alla sorgente, richiede la grandezza di ogni split
        Table_Source_Builder& withParallelism(int parallelism, uint64_t split_size){
            this->parallelism = parallelism;
            this->split_size = split_size;
            return *this;
        }

        //segna un EVENT TIME in cui il file di input è ordinato per timestamp
        Table_Source_Builder& withOrderedEventTime() {
            this->event_time = true;
            this->ordered = true;
            this->delay = 0;
            return *this;
        }

        //segna un EVENT TIME in cui si accetta del delay nei timestamp disordinati
        Table_Source_Builder& withWatermarkDelay(uint64_t del) {
            this->event_time = true;
            this->ordered = false;
            this->delay = del;
            return *this;
        }

        Table_Source_Builder& withHeader(){
            this->header = true;
            return *this;
        }

        auto build(){
            auto splits = make_splits(filepath, parallelism, split_size);

            //prima tupla letta per dare una base di normalizzazione ai timestamp
            uint64_t global_base_ts = 0;
            if (event_time) {
                std::ifstream f(filepath);
                std::string first_line;
                if (header) std::getline(f, first_line);
                if (std::getline(f, first_line)) {
                    TupleT dummy{};
                    parser_lambda(first_line, dummy, global_base_ts);
                }
                f.close();
            }

            Source_Functor<TupleT> functor = Source_Functor<TupleT>(
                filepath,
                header,
                parser_lambda,
                event_time,
                ordered,
                delay,
                global_base_ts,
                std::move(splits)
            );

            return wf::Source_Builder(functor)
                .withName(op_name)
                .withParallelism(parallelism)
                .build();
        }
};

#endif