from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, Set
from .draft import Draft
from .expressions import Expression, col, count, sum  , AggFuncType
from .operators import *
from .schema import Schema
from .table import Table, Query
from .windows import Interval, Window, WindowType
from .file_config import InputFileConfiguration
import json, os
if TYPE_CHECKING:
    from .table_env import TableEnvironment
    
class TimePolicy(Enum):
    """
    Politiche di gestione del tempo.
    - NO_POLICY: politica di default, non si possono usare finestre temporali ed intervalli, non supporta TimeCol nelle tabelle sorgente.
    - INGRESS_TIME: pone il timestamp pari all'attimo in cui la tupla viene processata, non supporta TimeCol nelle tabelle sorgente.
    - EVENT_TIME: il timestamp è ricavato tramite la TimeCol obbligatoria della tabella sorgente.
    """
    INGRESS_TIME = "INGRESS_TIME"
    EVENT_TIME = "EVENT_TIME"
    NO_POLICY = "NO_POLICY"

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

        self._sources_config[table_id] = file_config;
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
    # Esecuzione e Validazione Query
    # -------------------------------------------------------------------------
    def _serialize(self, op: Operator) -> Dict[str, Any]:
        """
        Ricostruisce la struttura ricorsiva della query a partire dall'operatore radice.
        Svolge controlli relativi alle politiche temporali.
        Unifica e valida gli operatori di group_by e select.
        """

        #le tabelle sorgenti si mettono direttamente come FromOp
        if isinstance(op, TableRefOp):
            if op.source_table_id in self._sources_config:
                source_cfg = self._sources_config[op.source_table_id]

                #controllo sulla politica temporale
                time_col = source_cfg.time_col
                if self.policy == TimePolicy.EVENT_TIME and time_col is None:
                    raise RuntimeError(
                        f"Con politica EVENT_TIME è necessario inserire una TimeCol in ogni tabella sorgente."
                    )
                
                if self.policy != TimePolicy.EVENT_TIME and time_col is not None:
                    raise RuntimeError(
                        f"Con politica {self.policy.value} è vietato inserire una TimeCol nelle tabelle sorgente."
                    )
               
                from_op = FromOp(
                    source_table_id=op.source_table_id,
                    file_config= source_cfg
                )
                return from_op.to_dict()

            if op.source_table_id not in self._tables:
                raise RuntimeError(f"La tabella {op.source_table_id} non è presente nell'ambiente.")

        #nei groupBy seguiti da select si mettono le aggregazioni nel JSON del groupBy
        if ( isinstance(op, GroupByOp)
            and op.window is not None
            and op.window.window_type == WindowType.TIME
            and self.policy == TimePolicy.NO_POLICY
            ):
            raise RuntimeError(
                f"Con NO_POLICY non si possono usare costrutti temporali."
                f" {op.window}"
            )

        #controllo la politica di tempo sull'attachment della join se presente 
        if isinstance(op, JoinOp) and op.attachment is not None:
            att = op.attachment

            if (self.policy  == TimePolicy.NO_POLICY
                and(
                    isinstance(att, Interval) 
                    or att.window_type == WindowType.TIME 
                    )
                ):
                raise RuntimeError(
                    f"Con politica temporale NO_POLICY non si possono usare costrutti temporali."
                    f"{att}"
                )
            
        node = op.to_dict()
        #se l'operatore ha dei parents li serializziamo ricorsivamente
        if op.parents:
            node["parents"] = [self._serialize(p) for p in op.parents]
            
        return node

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

    def execute(self, query: Query, output_dir: str = ".", rexecute: bool = False) -> Any:
        """
        Esegue i controlli dinamici iniziali sulla validità della query risalendo il grafo degli operatori,
        costruisce il JSON e invoca la generazione/compilazione C++.
        Il parametro "output_dir" è la directory in cui andranno inseriti i JSON, 
        di default è la dir corrente.
        Il parametro "rexecute" se impostato a True (di default è False) 
        fa rieseguire la serializzazione di file già presenti nella output_dir.
        Questo potrebbe portare problemi se tale file sta venendo parsato per un'altra query avviata precedentemente. 
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

        #creo la directory di output se non esiste
        os.makedirs(output_dir, exist_ok=True)

        #generazione del JSON per ogni query in queries_to_generate
        for q in queries_to_generate:
            file_path = os.path.join(output_dir, f"{q.table_id}.json")

            #controllo che il file non ci sia già, in tal caso non c'è bisogno di riscriverlo
            if (not rexecute) and os.path.exists(file_path):
                print(f"[TABLE API EXECUTE] '{file_path}' è già presente, non verrà ricalcolato.")
                continue

            #creo l'albero rapresentante la Query con un dizionario
            root = {
                "query_id": q.table_id,
                "root": self._serialize(q.root_operator),
            }

            #mapping di libreia dizionario -> json
            json_str = json.dumps(root, indent=4)

            #scrittura del file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        #TODO avviare l'esecuzione del codegen            

    def __repr__(self) -> str:
        return f"TableEnvironment(registered_tables={len(self._tables)})"
    