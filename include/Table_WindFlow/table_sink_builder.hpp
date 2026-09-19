#ifndef TABLE_SINK_BUILDER_HPP
#define TABLE_SINK_BUILDER_HPP

#include <string>
#include <fstream>
#include <iostream>
#include <memory>
#include <functional>
#include <optional>
#include <windflow.hpp>

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