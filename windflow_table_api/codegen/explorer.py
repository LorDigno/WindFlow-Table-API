from pathlib import Path
from typing import List, Dict
from jinja2 import Environment
from dataclasses import dataclass, field
from .schema_gen import SchemaGenerator, CppStruct
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator    
from .operation_nodes import OpNode, VisitContext, VisitResult

#---- Esploratore che coordina la visita dei nodi 

class GraphExplorer:
    """
    Classe il cui scopo è svolgere una visita del grafo per istanziare tutte le
    informazioni necessarie a generare il codice dal cpp. 
    """

    def __init__(
        self,
        jinja_env: Environment,
        output_dir: Path,
        parallelism: int = 1
    ):
        """
        Inizializza l'esploratore e i generatori sull'ambiente dato (aperto in condegen/templates/).
        """
        
        #parametri dell'ambiente
        self.sch_gen = SchemaGenerator(jinja_env)
        self.expr_tl = ExpressionTranslator(jinja_env)
        self.lambda_gen = LambdaGenerator(jinja_env)
        self.output_dir = output_dir
        self.parallelism = parallelism

        #gestione delle pipe
        self.pipe_counter = 0
        self.pipes: Dict[str, str] = {}
        self.pipe_order: List[str] = []

        #gestione delle operazioni prodotte
        #all'incirca superfluo in base a come vengono generati i node id.
        #   attualmente una sottoquery viene parsata una volta sola in OpNode e i TabRef non fanno altro che puntare alla sua root.
        #   questo comporta che un OpNode può venir visitato più volte quindi serve un altro contatore per avere nomi di variabili univoci.
        # (possibile utilità di questo sistema se mai verrà implementata una split di pipe in WF)
        self.operations_counter = 0             
        self.builders: List[str] = []

    def visit(self, root: OpNode, pipe: str = "pipe_0") -> CppStruct:
        """
        Metodo che visita i nodi ricorsivamente a partire dalla root.
        Viene svolta una visita posticipata così che sia rispettato l'oridnamento parziale degli operatori.
        Carica in self.builders i codici della creazione degli operatori.
        Carica in self.pipes i codici della creazione del PipeGraph da eseguire.
        Ogni sotto-visita rende l'output_struct corrente.
        """

        current_pipe = pipe
        to_merge = []                   #nomi delle pipe da unificare
        parent_structs = []             #nomi degli struct di output dei parents
        for p in root.parents:
            #di base si assume che il parent sia nella stessa pipe
            old_pipe = pipe
   
            #se ho più parents allora loro sono in pipes diverse (c'è da fare una merge)
            if len(root.parents) > 1:
                self.pipe_counter += 1
                old_pipe = f"pipe_{self.pipe_counter}"
                to_merge.append(old_pipe)

            #chiamata ricorsiva, accumulo gli struct di output
            parent_structs.append(self.visit(p, old_pipe))

        #creazione del contesto di visita
        context = VisitContext(
            pipe= current_pipe,
            parent_structs= parent_structs,
            to_merge_pipes= to_merge,
            sch_gen= self.sch_gen,
            expr_tl= self.expr_tl,
            lambda_gen= self.lambda_gen,
            operations_counter= self.operations_counter
        )

        #corpo della visita, da implementare diversamente in base all'operatore
        result: VisitResult = root.visit(context)

        #se la pipe viene inizializzata (op binari o from) la aggiungo all'ordine
        #concateno l'operazione corrente alla pipe
        if not current_pipe in self.pipe_order:
            self.pipe_order.append(current_pipe)
            self.pipes[current_pipe] = ""
        self.pipes[current_pipe] += result.pipe_addition

        #registro tutti i buider necessari all'operazione in ordine
        for b_string in result.emitted_builders:
            self.builders.append(b_string)

        #aggiorno il contatore in base a quante variabili sono state inizializzate 
        self.operations_counter += len(result.emitted_builders)

        return result.out_struct
        
#---- metodi pre refactoring di visita dei nodi 
"""
    def _visit_from(self, node: OpNode, pipe: str):
        #dati
        config = node.raw_dict.get("config", {})
        filepath = config.get("filepath", "stream_input.csv")
        time_col_dict = config.get("time_col")
        is_ordered = config.get("order", True)
        has_header = config.get("has_header", True)
        split_size= config.get("split_size", 0)

        delay = config.get("delay")
        delay = parse_duration_to_microseconds(delay) if delay else None

        #genero lo struct di output
        struct_out = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_out"],
            name_hint= "source_" + node.node_id
        )

        #funzione che esecue il parsing da dare al builder
        parser_func = LambdaGenerator.parser_lambda(
            struct_out= struct_out.struct_name,
            time_col_dict= time_col_dict,
            ordered_fields= [
                {"name": col_name, "type": col_type}
                for col_name, col_type in node.raw_dict["schema_out"].items()
            ]
        )

        self.node_counter += 1
        var_name = f"from_{self.node_counter}_op"

        #genero il builder
        builder_template = self._jinja_env.get_template("source_builder.jinja2")
        builder_code = builder_template.render(
            var_name=var_name,
            out_struct=struct_out.struct_name,
            filepath=filepath,
            parser_func= parser_func,
            op_name=node.node_id,
            has_header=has_header,
            event_time=time_col_dict is not None,
            is_ordered=is_ordered,
            delay=delay,
            par= self.parallelism,
            split_size= split_size
        )
        self.builders.append(builder_code)

        #aggiungo alla pipe
        self.pipes[pipe] = f"auto& {pipe} = topology.add_source({var_name})"
        if  pipe not in self.pipe_order:
            self.pipe_order.append(pipe)

        return struct_out

    def _visit_where(self, node: OpNode, pipe: str, parent_struct:CppStruct) -> CppStruct:
        #generazione lambda
        cond: str = self.expr_tl.translate_expr(node.raw_dict["condition"])
        filt_func = LambdaGenerator.where_lambda(
            in_struct= parent_struct.struct_name,
            condition= cond,
            in_var= "in"
        )

        self.node_counter += 1
        var_name = f"where_{self.node_counter}_op"

        #ottengo il codice del builder e lo registro
        template = self._jinja_env.get_template("where_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            filt_func= filt_func,
            in_struct= parent_struct.struct_name,
            op_name= node.node_id,
            par = self.parallelism
        )
        self.builders.append(builder)

        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

        return parent_struct
        
    def _visit_select(self, node: OpNode, pipe: str, parent_struct:CppStruct) -> CppStruct:
        #generazione schema di output
        #non necessitano ne di keyby forzato ne di hashing
        struct_out = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_out"],
            name_hint= node.node_id + "_struct_out",
        )

        #inferisco i mappings
        mappings: List[Tuple[str, str]] = []
        for e in node.raw_dict["expressions"]:
            #traduco l'espressione da assegnare
            value = self.expr_tl.translate_expr(e)

            target = e["alias"] if "alias" in e else e["name"]

            mappings.append((target, value))
        
        #generazione lambda
        map_func = LambdaGenerator.map_lambda(
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            mappings= mappings
        )

        self.node_counter += 1
        var_name = f"select_{self.node_counter}_op"

        #generazione builder
        template = self._jinja_env.get_template("select_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            map_func= map_func,
            op_name= node.node_id,
            par= self.parallelism
        )
        self.builders.append(builder)
        
        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

        return struct_out

    def _visit_group(self, node: OpNode, pipe: str, parent_struct:CppStruct) -> CppStruct:
        is_windowed = (node.raw_dict["op_type"] == "WINDOW_GROUP_BY")

        #ricavo le aggregazioni
        accs = []
        defaults = {}
        for a in node.raw_dict["aggregations"]:
            #accumulatore
            accs.append(self.expr_tl.translate_aggregate(a)) 

            #valore di dafault dell'accumulatore
            defaults[a["name"]] = get_aggregate_default(a["func"], a["data_type"])

        #gestione del keyBy
        key_struct = None
        key_lambda = None
        has_keys = len(node.raw_dict["keys"]) > 0
        keys = {}
        mappings = []
        if node.schema_in:
            input = node.schema_in
            iter = []
            if has_keys:
                iter = node.raw_dict["keys"]
            elif not has_keys and self.parallelism > 1:
                iter = input
            for k in iter:
                keys[k] = input[k]
                mappings.append((k, f"in.{k}"))                      

        if has_keys:
            key_struct = self.sch_gen.get_or_create_struct(
                schema_dict=keys,
                name_hint= node.node_id + "_key_struct",
                needs_hash=True
            )  

            key_lambda = LambdaGenerator.map_lambda(
                in_struct= parent_struct.struct_name,
                out_struct= key_struct.struct_name,
                mappings= mappings,
                input_var= "in"
            )

        #generazione schema di output
        struct_out = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_out"],
            name_hint= node.node_id + "_struct_out",
            needs_win= is_windowed,
            key_struct= key_struct,
            defaults= defaults
        )

        #genrazione della lambda
        lambda_func = LambdaGenerator.groupBy_lambda(
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            keys= node.raw_dict["keys"],
            accumulations= accs,
            in_var= "in",
            out_var= "out"
        )               

        #gestione delle finestre
        window = (None, None, None)
        if is_windowed:
            window = parse_window(node.raw_dict["window"])

        self.node_counter += 1
        var_name = f"group_{self.node_counter}_op"           

        #generazione builder
        template = self._jinja_env.get_template("group_builder.jinja2")
        builder = template.render(
            var_name = var_name,
            in_struct= parent_struct.struct_name,
            out_struct= struct_out.struct_name,
            lambda_func= lambda_func,

            needs_key= has_keys and (self.parallelism > 1),
            key_struct= key_struct.struct_name if key_struct else None,
            key_lambda= key_lambda,

            is_windowed= is_windowed,
            win_type= window[0],
            win_size= window[1],
            win_slide= window[2],

            op_name= node.node_id,
            par= self.parallelism
        )
        self.builders.append(builder)
                
        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

        return struct_out

    def _visit_distinct(self, node: OpNode, pipe: str, parent_struct:CppStruct) -> CppStruct:
        #richiede la hash sull'input per le hash_map
        parent_struct.needs_hash = True

        key_lambda = None
        if self.parallelism > 1:
            #genrazione della lambda di estrazione della chiave
            #in questo caso si tratta di rendere l'intero struct ricevuto in input

            key_lambda = (
                f"[](const {parent_struct.struct_name}& in) -> {parent_struct.struct_name}" + "{ return in; }"
            )

        self.node_counter += 1
        var_name = f"distinct_{self.node_counter}_op"

        #generazione builder (il distinct non richiede una lambda)
        template = self._jinja_env.get_template("distinct_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct= parent_struct.struct_name,
            key_struct= parent_struct.struct_name,
            key_lambda= key_lambda, 
            op_name= node.node_id,
            par = self.parallelism
        )
        self.builders.append(builder)
        
        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

        return parent_struct

    def _visit_join(
        self, 
        node: OpNode, 
        pipe: str, 
        to_merge: List[str],
        left_parent_struct: CppStruct,
        right_parent_struct: CppStruct
    ) -> CppStruct:
        is_windowed = node.op_type == "JOIN_WINDOWED"

        struct_out = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_out"],
            name_hint= node.node_id + "_struct_out"
        )

        #schema unificato
        joined_struct = self.sch_gen.struct_join(left_parent_struct, right_parent_struct)

        #inserzione nodi di unificazione schema
        #left
        left_mappings = []
        for f in left_parent_struct.fields:
            left_mappings.append((f.name, f"in.{f.name}"))

        self._emit_map(
            in_struct= left_parent_struct.struct_name,
            out_struct= joined_struct.struct_name,
            mappings= left_mappings,
            pipe= to_merge[0],
            name_hint= node.node_id + "_left_unifier",
        )

        #right
        right_mappings = []
        for f in right_parent_struct.fields:
            right_mappings.append((f.name, f"in.{f.name}"))
            
        self._emit_map(
            in_struct= right_parent_struct.struct_name,
            out_struct= joined_struct.struct_name,
            mappings= right_mappings,
            pipe= to_merge[1],
            name_hint= node.node_id + "_right_unifier",
        )

        #keyBy
        key_lambda = None
        key_struct = None
        if self.parallelism > 1 and node.schema_out:
            key_mappings = []
            keys = {}
            for k in node.raw_dict["keys"]:
                keys[k] = node.schema_out[k]
                key_mappings.append((k, f"in.{k}"))

            key_struct = self.sch_gen.get_or_create_struct(
                schema_dict= keys,
                name_hint= node.node_id + "_key_struct",
                needs_hash= True
            )

            key_lambda = LambdaGenerator.map_lambda(
                in_struct= joined_struct.struct_name,
                out_struct= key_struct.struct_name,
                mappings= key_mappings,
                input_var= "in"
            )

        #join mappings
        mappings = []
        for f in struct_out.fields:
            if f.name in [f.name for f in left_parent_struct.fields]:
                mappings.append((f.name, f"left.{f.name}"))
            else:
                mappings.append((f.name, f"right.{f.name}"))  

        #join lambda
        join_lambda = LambdaGenerator.join_lambda(
            input_struct= joined_struct.struct_name,
            out_struct= struct_out.struct_name,
            mappings= mappings,
            left_var= "left",
            right_var= "right",
        )

        #gestione finestre e intervalli
        window = (None, None, None)
        interval = (None, None)
        if is_windowed:
            window = parse_window(node.raw_dict["attachment"])
        else:   #si ha un intervallo
            interval = parse_interval(node.raw_dict["attachment"])

        self.node_counter += 1
        var_name = f"join_{self.node_counter}_op"

        #builder
        template = self._jinja_env.get_template("join_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct= joined_struct.struct_name,
            out_struct= struct_out.struct_name,
            join_func= join_lambda,

            needs_key= self.parallelism > 1,
            key_lambda= key_lambda,
            key_struct= key_struct.struct_name if key_struct else None,

            is_windowed= is_windowed,
            win_size= window[1],
            win_slide= window[2],
            lower= interval[0],
            upper= interval[1],

            op_name= node.node_id,
            par= self.parallelism
        )
        self.builders.append(builder)

        #merge delle pipe degli stream congiunti e creazione current_pipe
        template = self._jinja_env.get_template("merge_pipes.jinja2")
        pipe_str = template.render(
            out_pipe= pipe,
            branches_var= f"{pipe}_branches",
            branches= to_merge,
            topology_name= "topology"
        )
        self.pipes[pipe] = pipe_str
        if pipe not in self.pipe_order:
            self.pipe_order.append(pipe)

        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

        return struct_out

    def _visit_union(
        self, 
        node: OpNode, 
        pipe: str, 
        to_merge: List[str], 
        parent_struct:CppStruct
    ) -> CppStruct:
        distinct = (node.op_type == "UNION")

        template = self._jinja_env.get_template("merge_pipes.jinja2")
        pipe_str = template.render(
            out_pipe= pipe,
            branches_var= f"{pipe}_branches",
            branches= to_merge,
            topology_name= "topology"
        )
        self.pipes[pipe] = pipe_str
        if pipe not in self.pipe_order:
            self.pipe_order.append(pipe)

        if distinct:
            d_node = OpNode(
                node_id= node.node_id + "_union_distinct",
                op_type= "DISTINCT",
                raw_dict= {"schema_in": node.raw_dict["schema_out"]}
            )
            self._visit_distinct(d_node, pipe, parent_struct)

        return parent_struct    

    def _visit_intersect(
        self, 
        node: OpNode, 
        pipe: str, 
        to_merge: List[str], 
        parent_struct:CppStruct
    ) -> CppStruct:
        is_all = (node.op_type == "INTERSECT_ALL")

        #necessario per le hash_map
        parent_struct.needs_hash = True
        tagged_struct = f"Tagged_Tuple<{parent_struct.struct_name}>"
        
        #tagging del left stream
        left_mappings = [
            ("data", "in"),
            ("tag", "0"),
        ]
        self._emit_map(
            in_struct= parent_struct.struct_name,
            out_struct= tagged_struct,
            mappings= left_mappings,
            pipe= to_merge[0],
            name_hint= f"{node.node_id}_left_tagger"
        )

        #tagging del right stream
        right_mappings = [
            ("data", "in"),
            ("tag", "1"),
        ]
        self._emit_map(
            in_struct= parent_struct.struct_name,
            out_struct= tagged_struct,
            mappings= right_mappings,
            pipe= to_merge[1],
            name_hint= f"{node.node_id}_right_tagger"
        )

        self.node_counter += 1
        var_name = f"intersect_{self.node_counter}_op"

        #builder
        template = self._jinja_env.get_template("intersect_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct = parent_struct.struct_name,
            is_all= is_all,
            op_name= node.node_id,
            par = self.parallelism
        )
        self.builders.append(builder)

        #eseguo il merge delle pipes
        template = self._jinja_env.get_template("merge_pipes.jinja2")
        pipe_str = template.render(
            out_pipe= pipe,
            branches_var= f"{pipe}_branches",
            branches= to_merge,
            topology_name= "topology"
        )
        self.pipes[pipe] = pipe_str

        #aggiungo l'operatore d'intersect
        self.pipes[pipe] += f".add({var_name})"
        if pipe not in self.pipe_order:
            self.pipe_order.append(pipe)

        return parent_struct

    def _emit_map(
        self,
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        pipe: str,
        name_hint: str,
    ):
        
        Genera e inietta direttamente un operatore di adattamento nella pipe indicata.
        Utilizzata da visit_join e visit_intersect per l'unificazione/tagging degli struct.

        map_func = LambdaGenerator.map_lambda(
            in_struct=in_struct,
            out_struct=out_struct,
            mappings=mappings,
            input_var="in",
        )

        self.node_counter += 1
        var_name = f"map_{self.node_counter}_op"

        template = self._jinja_env.get_template("select_builder.jinja2")
        builder = template.render(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            map_func=map_func,
            op_name=name_hint,
            par=self.parallelism,
        )
        self.builders.append(builder)

        self.pipes[pipe] += f".add({var_name})"

    def add_sink(
        self,
        final_struct: CppStruct,
        filepath: str = "output.csv",
        has_header: bool = True,
        pipe: str = "pipe_0",
        sink_name: str = "Table_Sink"
    ) -> None:
        
        Genera il Table_Sink_Builder tipizzato sull'ultimo struct del DAG,
        lo registra in self.builders e chiude la catena della pipe specificata.
        
        #preparazione dell'header
        header_str = ", ".join(f.name for f in final_struct.fields) if has_header else None

        #generazione della lambda
        formatter_func = LambdaGenerator.sink_lambda(
            final_struct.struct_name,
            fields= [{"name": f.name} for f in final_struct.fields]
        )

        self.node_counter += 1
        var_name = f"sink_{self.node_counter}_op"

        #genero il builder
        builder_template = self._jinja_env.get_template("sink_builder.jinja2")
        builder_code = builder_template.render(
            var_name=var_name,
            in_struct=final_struct.struct_name,
            filepath=filepath,
            formatter_func=formatter_func,
            header_str=header_str,
            op_name= sink_name,
            par= self.parallelism
        )
        self.builders.append(builder_code)

        #aggiunta alla pipe        
        self.pipes[pipe] += f".add_sink({var_name})"
"""