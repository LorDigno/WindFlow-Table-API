import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

@dataclass
class OpNode:
    """
    Rappresentazione di un nodo operatore all'interno del grafo.
    """

    node_id: str
    op_type: str
    raw_dict: Dict[str, Any]
    parents: List['OpNode'] = field(default_factory=list)
    children: List['OpNode'] = field(default_factory=list)
    schema_in: Optional[Dict[str, Any]] = None
    schema_out: Optional[Dict[str, Any]] = None
    #gli operatori binari che non hanno schema_in li ricavano dai genitori

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        if isinstance(other, OpNode):
            return self.node_id == other.node_id
        return False

@dataclass
class ParsedGraph:
    """Contenitore per il grafo analizzato."""

    query_id: str
    target_root: OpNode              

class JsonParser:
    """
    Legge il file JSON e costruisce il grafo degli operatori 
    pronto per la generazione di codice C++.
    """

    def __init__(self, json_dir: Path):
        self.json_dir = Path(json_dir)
        self.loaded_queries: Set[str] = set()
        self.root_nodes: Dict[str, OpNode] = {}
        self.node_registry: Dict[str, OpNode] = {}
        self._node_counter = 0

    def _gen_node_id(self, query_id: str, op_type: str) -> str:
        """
        Genera l'id di un nodo in base alla sua operazione, 
        la query di appartenenza e il conteggio globale dei nodi.
        """

        self._node_counter += 1
        return f"{query_id}_{op_type.lower()}_{self._node_counter}"

    def parse_query(self, query_id: str) -> ParsedGraph:
        """
        Punto d'ingresso principale: carica <query_id>.json, traversa i nodi
        e restituisce il grafo ordinato topologicamente.
        """

        #fetch del file json
        json_path = self.json_dir / f"{query_id}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"File JSON AST non trovato: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            query_dict = json.load(f)

        self.loaded_queries.add(query_id)

        #estraggo l'ultimo nodo del grafo
        root_raw = query_dict.get("root")
        if not root_raw:
            raise ValueError(f"JSON non valido: manca il campo 'root' in {query_id}.json")

        #costruzione ricorsiva del grafo a partire dall'ultimo nodo
        root_node = self._build_node_recursive(query_id, root_raw)
        self.root_nodes[query_id] = root_node

        return ParsedGraph(
            query_id=query_id,
            target_root= root_node
        )

    def _build_node_recursive(self, query_id: str, op_dict: Dict[str, Any]) -> OpNode:
        """
        Trasforma ricorsivamente la struttura JSON annidata dei 'parents'
        in OpNode interconnessi.
        """

        op_type = op_dict.get("op_type", "UNKNOWN")

        #passi ad esplorare un'altra query
        if op_type == "TAB_REF":
            return self._handle_tab_ref(op_dict)

        #generazione dell'id del nodo
        op_name = op_dict.get("op_name") or self._gen_node_id(query_id, op_type)

        #creazione e registrazione del nodo
        node = OpNode(
            node_id=op_name,
            op_type=op_type,
            raw_dict=op_dict,
            schema_in=op_dict.get("schema_in"),
            schema_out=op_dict.get("schema_out")
        )
        self.node_registry[op_name] = node

        #esplorazione ricorsiva dei genitori
        for p_dict in op_dict.get("parents", []):
            parent_node = self._build_node_recursive(query_id, p_dict)
            node.parents.append(parent_node)
            parent_node.children.append(node)

        return node

    def _handle_tab_ref(self, ref_dict: Dict[str, Any]) -> OpNode:
        """
        Gestisce i nodi TAB_REF, le sotto-query, e ne parsa il JSON corrispondente.
        """

        source_id = str(ref_dict.get("source_id"))
        sub_query_file = self.json_dir / f"{source_id}.json"

        #se il file è assente si solleva un'eccezione
        if not sub_query_file.exists():
            raise FileNotFoundError(f"Il file {sub_query_file} non è stato trovato.") 

        #se non si è già eleaborata si esplora e si rende il root
        if source_id not in self.loaded_queries:
            sub_dag = self.parse_query(source_id)
            return sub_dag.target_root

        #se la query è già stata visitata rendo la sua root (ovvero l'ultimo nodo)
        return self.root_nodes[source_id]

    def _collect_all_nodes(self, root: OpNode) -> List[OpNode]:
        """Raccoglie tutti i nodi traversando a ritroso le dipendenze."""

        visited: Set[OpNode] = set()
        stack = [root]

        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
                stack.extend(curr.parents)

        return list(visited)
