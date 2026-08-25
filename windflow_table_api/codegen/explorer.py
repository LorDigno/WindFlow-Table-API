from pathlib import Path
from typing import List, Optional, Dict
from jinja2 import Environment, FileSystemLoader
from .parser import ParsedGraph, OpNode
from .schema_gen import SchemaGenerator
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator        

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
            #self._visit_from(root)
            pass
        elif op_type == "WHERE":
            self._visit_where(root, current_pipe)
        elif op_type == "SELECT":
            self._visit_select(root, current_pipe)
        elif op_type in ("GROUP_BY", "WINDOW_GROUP_BY"):
            self._visit_group(root, current_pipe)
        elif op_type in ("DISTINCT"):
            self._visit_distinct(root, current_pipe)    
        elif op_type in ("JOIN", "INTERVAL_JOIN", "WINDOW_JOIN"):
            self._visit_join(root, current_pipe, to_merge)
        elif op_type in ("UNION", "UNION_ALL"):
            self._visit_union(root, current_pipe, to_merge)    
        elif op_type in ("INTERSECT", "INTERSECT_ALL"):
            self._visit_intersect(root, current_pipe, to_merge)    


    def _visit_where(self, node: OpNode, pipe: str):
        #genero lo schema
        #non richiede altro dato che la filter anche parallela non richiede hashing o keyBy
        struct = self.sch_gen.get_or_create_struct(
            node.raw_dict["schema_in"],
            node.node_id + "_struct",
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
            op_name= f"where_{node.node_id}",
            par = self.parallelism
        )
        self.builders.append(builder)

        #aggiungo alla pipe l'operatore
        self.pipes[pipe] += f".add({var_name})"
        

    def _visit_select(self, node: OpNode, pipe: str):
        pass

    def _visit_group(self, node: OpNode, pipe: str):
        pass

    def _visit_distinct(self, node: OpNode, pipe: str):
        pass

    def _visit_join(self, node: OpNode, pipe: str, to_merge: List[str]):
        pass

    def _visit_union(self, node: OpNode, pipe: str, to_merge: List[str]):
        pass

    def _visit_intersect(self, node: OpNode, pipe: str, to_merge: List[str]):
        pass


        