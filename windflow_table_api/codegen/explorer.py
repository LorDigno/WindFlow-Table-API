from pathlib import Path
from typing import List, Dict
from jinja2 import Environment
from dataclasses import dataclass, field
from .schema_gen import SchemaGenerator, CppStruct
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator    
from .operation_nodes import OpNode, VisitContext, VisitResult
from .builder_generator import BuilderGenerator

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

        #genratori via templating
        self.sch_gen = SchemaGenerator(jinja_env)
        self.expr_tl = ExpressionTranslator(jinja_env)
        self.lambda_gen = LambdaGenerator(jinja_env)
        self.build_gen = BuilderGenerator(jinja_env)

        #parametri dell'ambiente
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
            build_gen= self.build_gen,
            operations_counter= self.operations_counter,
            par= self.parallelism
        )

        #corpo della visita, da implementare diversamente in base all'operatore
        result: VisitResult = root.visit(context)

        #se la pipe viene inizializzata (op binari o from) la aggiungo all'ordine
        #concateno l'operazione corrente alla pipe
        if not current_pipe in self.pipe_order:
            self.pipe_order.append(current_pipe)
            self.pipes[current_pipe] = ""
        for pipe_name in result.pipe_additions:
            self.pipes[pipe_name] += result.pipe_additions[pipe_name]

        #registro tutti i buider necessari all'operazione in ordine
        for b_string in result.emitted_builders:
            self.builders.append(b_string)

        #aggiorno il contatore in base a quante variabili sono state inizializzate 
        self.operations_counter += len(result.emitted_builders)

        return result.out_struct
 