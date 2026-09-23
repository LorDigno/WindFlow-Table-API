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
        uint64_t max_ts = 0, global_epoch = 0 , last_wm = 0;
        bool first_wm = true;

        void process_ordered(uint64_t& current_ts, uint64_t& current_wm) {
            //normalizza secondo la prima tupla
            current_ts = (current_ts >= global_epoch) ? (current_ts - global_epoch) : 0;
            current_wm = current_ts;
        }

        void process_out_of_order(uint64_t& current_ts, uint64_t& current_wm) {
            //normalizza secondo il delay
            current_ts = (current_ts >= global_epoch) 
                            ? (current_ts - global_epoch) 
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
            global_epoch(base_ts),
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

            std::cout << "[SRC" << ctx.getReplicaIndex() << "] File " << file_path << " aperto." << std::endl;

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
        uint64_t global_epoch = 0;      //timestamp di normalizzazione globale

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
        Table_Source_Builder& withOrderedEventTime(uint64_t epoch) {
            this->event_time = true;
            this->ordered = true;
            this->delay = 0;
            this->global_epoch = epoch;
            return *this;
        }

        //segna un EVENT TIME in cui si accetta del delay nei timestamp disordinati
        Table_Source_Builder& withDelayedEventTime(uint64_t epoch, uint64_t del) {
            this->event_time = true;
            this->ordered = false;
            this->delay = del;
            this->global_epoch = epoch;
            return *this;
        }

        Table_Source_Builder& withHeader(){
            this->header = true;
            return *this;
        }

        auto build(){
            auto splits = make_splits(filepath, parallelism, split_size);
            Source_Functor<TupleT> functor = Source_Functor<TupleT>(
                filepath,
                header,
                parser_lambda,
                event_time,
                ordered,
                delay,
                global_epoch,
                std::move(splits)
            );

            return wf::Source_Builder(functor)
                .withName(op_name)
                .withParallelism(parallelism)
                .build();
        }
};

#endif