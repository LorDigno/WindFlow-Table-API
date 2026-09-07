from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from .operators import *
from .schema import Schema
from .table import Table, Query
from .windows import Interval, WindowType
from .file_config import InputFileConfiguration
from windflow_table_api.runtime import Executor
from windflow_table_api.codegen import generate_code
from .job_handle import JobHandle
from windflow_table_api import TimePolicy
import json

class TableEnvironment:
    """
    Ambiente di esecuzione della Table API per WindFlow.
    Traccia le sorgenti di dati, assegna gli ID univoci alle tabelle,
    mantiene il registro dei flussi e gestisce la validazione ed esecuzione delle query.
    Il parametro "par" indica il parallelismo che verrà assegnato agli operatori.
    Il parametro "policy" come verrà gestito il tempo.
    """

    def __init__(self, 
                 par: int = 1, 
                 policy: TimePolicy = TimePolicy.NO_POLICY
        ) -> None:
        self._table_counter: int = 0
        self._tables: Dict[str, Table] = {}
        self._sources_config: Dict[str, InputFileConfiguration] = {}
        self.par = par
        self.policy = policy

    def _generate_table_id(self, prefix: str = "tab") -> str:
        """Genera un identificativo univoco progressivo per ogni tabella o query nell'ambiente."""

        self._table_counter += 1
        return f"{prefix}_{self._table_counter}"

    def table_from_file(
            self, 
            file_config: InputFileConfiguration,
            name: Optional[str] = None
        ) -> Table:
        """
        Crea uno Data Stream sorgente a partire da un file.
        Istanzia una Table associata allo schema, le assegna un ID univoco e la registra.
        Deve avere "time_col" solo e soltanto se la politica temporale è EVENT_TIME.
        """

        if self.policy == TimePolicy.EVENT_TIME and file_config.time_col is None:
            raise RuntimeError(
                f"Con politica EVENT_TIME è necessario inserire una TimeCol in ogni tabella sorgente."
            )

        if self.policy != TimePolicy.EVENT_TIME and file_config.time_col is not None:
            raise RuntimeError(
                f"Con politica {self.policy.value} è vietato inserire una TimeCol nelle tabelle sorgente."
            )

        if name:
            if name in self._tables:
                raise ValueError(f"Una tabella con il nome '{name}' è già registrata nell'ambiente.")
            
            table_id = name
            self._table_counter += 1

        else:
            table_id = self._generate_table_id("source_stream_file")
        
        table = Table(schema=file_config.schema, table_id=table_id, env=self)
        self._tables[table_id] = table

        self._sources_config[table_id] = file_config
        return table

    # -------------------------------------------------------------------------
    # Registrazione e Gestione Tabelle
    # -------------------------------------------------------------------------

    def get_table(self, name: str) -> Table:
        """Recupera una tabella registrata nell'ambiente tramite il suo nome."""

        if name not in self._tables:
            raise KeyError(f"Nessuna tabella trovata con il nome '{name}'.")
        
        return self._tables[name]

    def get_source_config(self, source_id: str) -> Optional[InputFileConfiguration]:
        """
        Recupera la configurazione fisica della sorgente dal catalogo.
        Se non è presente rende None;
        """

        return self._sources_config.get(source_id)

    def create_query(self, schema: Schema, parent_table: str, root_op: Operator,
                     name: Optional[str] = None) -> Query:
        """
        Crea e registra nell'ambiente una nuova Table derivata a seguito dell'applicazione di una query.
        Se il Draft aveva un nome quello sarà il table_id della Query creata.
        """

        if name:
            if name in self._tables:
                raise ValueError(f"Una tabella con il nome '{name}' è già registrata nell'ambiente.")
                        
            table_id = name
            self._table_counter += 1
        else:    
            table_id = self._generate_table_id(f"{parent_table}_query")

        query_table = Query(
            schema=schema, 
            table_id=table_id, 
            parent_table=parent_table,
            env=self, 
            root_operator=root_op
        )

        self._tables[table_id] = query_table
        return query_table

    # -------------------------------------------------------------------------
    # Serializzazione e Validazione Query
    # -------------------------------------------------------------------------

    def _serialize_dag(self, op: Operator) -> Dict[str, Any]:
        """
        Serializza (via to_dict) l'operatore e chiama ricorsivamente ai parents.
        Gli operatori di TableRef che sono sorgenti vengono sostituiti con FromOp.
        Presuppone che il grafo sia stato validato tramite _validate_dag.
        """

        #sostituzione di TableRef -> From per le sorgenti
        if isinstance(op, TableRefOp) and op.source_table_id in self._sources_config:
            file_cfg = self._sources_config[op.source_table_id]
            from_op = FromOp(source_table_id=op.source_table_id, file_config=file_cfg)
            return from_op.to_dict()

        #ricava il dizionario di se e dei parents
        node_dict = op.to_dict()
        if op.parents:
            node_dict["parents"] = [self._serialize_dag(p) for p in op.parents]

        return node_dict

    def _validate_operator_semantics(self, op: Operator) -> None:
        """
        Valida i vincoli di policy temporale e l'integrità del catalogo per il singolo nodo.
        """

        #controllo sulle policy temporali
        if self.policy == TimePolicy.NO_POLICY:
            if (
                isinstance(op, GroupByOp)
                and op.window
                and op.window.window_type == WindowType.TIME
            ):
                raise ValueError(
                    "Con TimePolicy.NO_POLICY non sono ammesse finestre temporali:"
                    f" {op.window}"
                )

            if isinstance(op, JoinOp) and op.attachment is not None:
                att = op.attachment
                if (
                    isinstance(att, Interval)
                    or getattr(att, "window_type", None) == WindowType.TIME
                ):
                    raise ValueError(
                        "Con TimePolicy.NO_POLICY non sono ammessi intervalli o finestre"
                        f" temporali nella Join: {att}"
                    )

        #controllo della presenza delle tabelle
        if isinstance(op, TableRefOp):
            if (
                op.source_table_id not in self._sources_config
                and op.source_table_id not in self._tables
            ):
                raise KeyError(
                    f"La tabella '{op.source_table_id}' referenziata nella query non è"
                    " presente nell'ambiente."
                )

    def _validate_dag(self, root_op: Operator) -> None:
        """
        Attraversa l'albero ed esegue la validazione semantica su tutti gli operatori.
        """

        self._validate_operator_semantics(root_op)
        for parent in root_op.parents:
            self._validate_dag(parent)

    # -------------------------------------------------------------------------
    # Orchestrazione generale dell'esecuzione
    # -------------------------------------------------------------------------  
     
    def _collect_referenced_queries(self, op: Operator, collected: Set[str]) -> None:
        """
        Attraversa il grafo degli operatori per trovare tutte le Query 
        intermedie collegate tramite TableRefOp.
        """

        #caso di un riferimento per capire se è sorgente e se l'ho già vista
        if (isinstance(op, TableRefOp) 
            and op.source_table_id not in self._sources_config #non è una sorgente
            and op.source_table_id in self._tables             
            ):
                parent_table = self._tables[op.source_table_id]
                if isinstance(parent_table, Query) and parent_table.table_id not in collected:
                    #salvo la query come da fare
                    collected.add(parent_table.table_id)

                    #ricorsione sui genitori della query trovata
                    self._collect_referenced_queries(parent_table.root_operator, collected)

        for p in op.parents:
            #ricorsione sugli operatori genitori
            self._collect_referenced_queries(p, collected)

    def execute(self, 
        query: Query, 
        output_dir: str = ".", 
        rexecute: bool = False,
        sync: bool = False
    ) -> JobHandle:
        """
        Esegue i controlli dinamici iniziali sulla validità della query risalendo il grafo degli operatori,
        costruisce il JSON e invoca la generazione/compilazione C++.
        Il parametro "output_dir" è la directory in cui andranno inseriti i JSON, 
        di default è la dir corrente.
        Il parametro "rexecute" se impostato a True (di default è False) 
        fa rieseguire la serializzazione di file già presenti nella output_dir.
        Questo potrebbe portare problemi se tale file sta venendo parsato per un'altra query avviata precedentemente.
        Rende un oggetto JobHandle per il monitoraggio. 
        """

        #trovo tutte le query necessarie all'esecuzione di quella richiesta
        referenced_ids: Set[str] = set()
        self._collect_referenced_queries(query.root_operator, referenced_ids)

        queries_to_generate: List[Query] = []
        for q_id in referenced_ids:
            table = self._tables[q_id]
            assert isinstance(table, Query), f"La tabella '{q_id}' dovrebbe essere una Query"
            queries_to_generate.append(table)
        queries_to_generate.append(query)

        #creazione/individuazione directory d'output
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        #generazione del JSON per ogni query in queries_to_generate
        for q in queries_to_generate:
            #validazione del grafo
            self._validate_dag(q.root_operator)

            file_path = out_path / f"{q.table_id}.json"

            #controllo che il file non ci sia già, in tal caso non c'è bisogno di riscriverlo
            if (not rexecute) and file_path.exists():
                print(f"[TABLE API EXECUTE] '{file_path}' è già presente, non verrà ricalcolato.")
                continue

            #creo l'albero rapresentante la Query con un dizionario
            root = {
                "query_id": q.table_id,
                "root": self._serialize_dag(q.root_operator),
            }

            #mapping di libreia dizionario -> json
            json_str = json.dumps(root, indent=4)

            #scrittura del file json
            file_path.write_text(json_str, encoding="utf-8")

        #chiamata alla generazione del codice
        generate_code(
            query_id=query.table_id,
            time_policy=self.policy.name,
            parallelism=self.par,
            json_dir=out_path,
        )

        #compilazione ed esecuzione
        executor = Executor(work_dir=out_path)
        handle = executor.run_query(query.table_id)

        #aspetto se si vuole sincrono
        if sync:
            handle.wait()

        return handle            

    def __repr__(self) -> str:
        return f"TableEnvironment(registered_tables={len(self._tables)})"
    