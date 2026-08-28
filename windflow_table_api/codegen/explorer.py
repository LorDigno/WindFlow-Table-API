from pathlib import Path
from typing import List, Dict, Tuple
from jinja2 import Environment, FileSystemLoader
from .parser import OpNode
from .schema_gen import SchemaGenerator, CppStruct, CppField
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator    
from .utility import get_aggregate_default, parse_window, parse_interval

class GraphExplorer:
    """
    Classe il cui scopo è svolgere una visita del grafo per istanziare tutte le
    informazioni necessarie a generare il codice dal cpp. 
    """

    def __init__(
        self,
        sch_gen: SchemaGenerator,
        expr_tl: ExpressionTranslator,
        output_dir: Path,
        parallelism: int = 1
    ):
        #parametri dell'ambiente
        self.sch_gen = sch_gen
        self.expr_tl = expr_tl
        self.output_dir = output_dir
        self.parallelism = parallelism

        #gestione delle pipe
        self.pipe_counter = 0
        self.pipes: Dict[str, str] = {"pipe_1": ""}

        #gestione dei nodi
        self.node_counter = 0
        self.builders: List[str] = []

        #setup di jinja
        templates_dir = Path(__file__).parent / "templates" / "nodes"
        self._jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def visit(self, root: OpNode, pipe: str = "pipe_0"):
        """
        Metodo che visita i nodi ricorsivamente a partire dalla root.
        Viene svolta una visita posticipata così che sia rispettato l'oridnamento parziale degli operatori.
        Carica in self.builders i codici della creazione degli operatori.
        Carica in self.pipes i codici della creazione del PipeGraph da eseguire.
        """

        current_pipe = pipe
        to_merge = []                   #nomi delle pipe da unificare
        for p in root.parents:
            #gestione delle pipes
            old_pipe = pipe
   
            #se ho più parents allora loro sono in pipes diverse
            if len(root.parents) > 1:
                self.pipe_counter += 1
                old_pipe = f"pipe_{self.pipe_counter}"
                to_merge.append(old_pipe)

            #chiamata ricorsiva
            self.visit(p, old_pipe)

        #corpo della visita, da implementare diversamente in base all'operatore
        #eseguito per la prima volta quando trova un from senza parents
        op_type = root.op_type
    
        if op_type == "FROM":
            self._visit_from(root, current_pipe)
        elif op_type == "WHERE":
            self._visit_where(root, current_pipe)
        elif op_type == "SELECT":
            self._visit_select(root, current_pipe)
        elif op_type in ("GROUP_BY", "WINDOW_GROUP_BY"):
            self._visit_group(root, current_pipe)
        elif op_type in ("DISTINCT"):
            self._visit_distinct(root, current_pipe)    
        elif op_type in ("JOIN_INNER", "JOIN_INTERVAL", "JOIN_WINDOW"):
            self._visit_join(root, current_pipe, to_merge)
        elif op_type in ("UNION", "UNION_ALL"):
            self._visit_union(root, current_pipe, to_merge)    
        elif op_type in ("INTERSECT", "INTERSECT_ALL"):
            self._visit_intersect(root, current_pipe, to_merge)    

    def _visit_from(self, node: OpNode, pipe: str):
        self.pipes[pipe] = f"auto {pipe} = topology.add_source(***)"

    def _visit_where(self, node: OpNode, pipe: str):
        #genero lo schema
        #non richiede altro dato che la filter anche parallela non richiede hashing o keyBy
        struct = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_in"],
            name_hint= node.node_id + "_struct",
        )

        #generazione lambda
        cond: str = self.expr_tl.translate_expr(node.raw_dict["condition"])
        filt_func = LambdaGenerator.where_lambda(
            in_struct= struct.struct_name,
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
            in_struct= struct.struct_name,
            op_name= node.node_id,
            par = self.parallelism
        )
        self.builders.append(builder)

        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"
        
    def _visit_select(self, node: OpNode, pipe: str):
        #generazione schemi di input e output
        #non necessitano ne di keyby forzato ne di hashing
        struct_in = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_in"],
            name_hint= node.node_id + "_struct_in",
        )
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
            in_struct= struct_in.struct_name,
            out_struct= struct_out.struct_name,
            mappings= mappings
        )

        self.node_counter += 1
        var_name = f"select_{self.node_counter}_op"

        #generazione builder
        template = self._jinja_env.get_template("select_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct= struct_in.struct_name,
            out_struct= struct_out.struct_name,
            map_func= map_func,
            op_name= node.node_id,
            par= self.parallelism
        )
        self.builders.append(builder)
        
        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

    def _visit_group(self, node: OpNode, pipe: str):
        is_windowed = (node.raw_dict["op_type"] == "WINDOW_GROUP_BY")

        #ricavo le aggregazioni
        accs = []
        defaults = {}
        for a in node.raw_dict["aggregations"]:
            #accumulatore
            accs.append(self.expr_tl.translate_aggregate(a)) 

            #valore di dafault dell'accumulatore
            defaults[a["name"]] = get_aggregate_default(a["func"], a["data_type"])

        #generazione schema input
        struct_in = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_in"],
            name_hint= node.node_id + "_struct_in",
        )

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
        
        key_struct = self.sch_gen.get_or_create_struct(
            schema_dict=keys,
            name_hint= node.node_id + "_key_struct",
            needs_hash=True
        )  

        key_lambda = LambdaGenerator.map_lambda(
            in_struct= struct_in.struct_name,
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
            in_struct= struct_in.struct_name,
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
            in_struct= struct_in.struct_name,
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

    def _visit_distinct(self, node: OpNode, pipe: str):
        #generazione schema 
        #richiede l'hash per le hash_map
        schema = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_in"],
            name_hint= node.node_id + "_struct_in",
            needs_hash= True
        )

        key_lambda = None
        if self.parallelism > 1:
            #genrazione della lambda di estrazione della chiave
            #in questo caso si tratta di rendere l'intero struct ricevuto in input

            key_lambda = (
                f"[](const {schema.struct_name}& in) -> {schema.struct_name}" + "{ return in; }"
            )

        self.node_counter += 1
        var_name = f"distinct_{self.node_counter}_op"

        #generazione builder (il distinct non richiede una lambda)
        template = self._jinja_env.get_template("distinct_builder.jinja2")
        builder = template.render(
            var_name= var_name,
            in_struct= schema.struct_name,
            key_struct= schema.struct_name,
            key_lambda= key_lambda, 
            op_name= node.node_id,
            par = self.parallelism
        )
        self.builders.append(builder)
        
        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

    def _visit_join(self, node: OpNode, pipe: str, to_merge: List[str]):
        is_windowed = node.op_type == "JOIN_WINDOWED"

        #schemi del left stream e right stream
        left_struct = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["tab1_schema"],
            name_hint= node.node_id + "_left_struct",
        )

        right_struct = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["tab2_schema"],
            name_hint= node.node_id + "_right_struct",
        )

        struct_out = self.sch_gen.get_or_create_struct(
            schema_dict= node.raw_dict["schema_out"],
            name_hint= node.node_id + "_struct_out"
        )

        #schema unificato
        joined_struct = self.sch_gen.struct_join(left_struct, right_struct)

        #inserzione nodi di unificazione schema
        #left
        left_mappings = []
        for f in left_struct.fields:
            left_mappings.append((f.name, f"in.{f.name}"))

        self._emit_map(
            in_struct= left_struct.struct_name,
            out_struct= joined_struct.struct_name,
            mappings= left_mappings,
            pipe= to_merge[0],
            name_hint= node.node_id + "_left_unifier",
        )

        #right
        right_mappings = []
        for f in right_struct.fields:
            right_mappings.append((f.name, f"in.{f.name}"))
            
        self._emit_map(
            in_struct= right_struct.struct_name,
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
            if f.name in [f.name for f in left_struct.fields]:
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

        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"

    def _visit_union(self, node: OpNode, pipe: str, to_merge: List[str]):
        distinct = (node.op_type == "UNION")

        template = self._jinja_env.get_template("merge_pipes.jinja2")
        pipe_str = template.render(
            out_pipe= pipe,
            branches_var= f"{pipe}_branches",
            branches= to_merge,
            topology_name= "topology"
        )
        self.pipes[pipe] = pipe_str

        if distinct:
            d_node = OpNode(
                node_id= node.node_id + "_union_distinct",
                op_type= "DISTINCT",
                raw_dict= {"schema_in": node.raw_dict["schema_out"]}
            )
            self._visit_distinct(d_node, pipe)

    def _visit_intersect(self, node: OpNode, pipe: str, to_merge: List[str]):
        self.pipes[pipe] = "intersect"

    def _emit_map(
        self,
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        pipe: str,
        name_hint: str,
    ):
        """
        Genera e inietta direttamente un operatore di adattamento nella pipe indicata.
        Utilizzata da visit_join e visit_intersect per l'unificazione/tagging degli struct.
        """

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
