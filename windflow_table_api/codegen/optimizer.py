from .operation_nodes import *
from .parser import ParsedGraph
from typing import Dict, Any, List, Set
from ..object_names import ExprType

def remove_and_relink(
    current_node:UnaryNode, 
    graph:Optional[ParsedGraph] = None
    ) -> OpNode:
    """
    Rimuove il nodo attuale e lo sostituisce con i propri parent nella lista dei parent del nodo precedente.
    Supportato solo per operatori unari UnaryNode.
    Se tale nodo è la radice del ParsedGraph la cambia. (non dovrebbe mai capitare al sink).
    Rende il nodo parent del current
    """
    if len(current_node.parents) != 1:
        raise ValueError(
            f"remove_and_relink supporta solo nodi con 1 genitore, trovati: {len(current_node.parents)}"
        )

    upstream_node = current_node.parents[0]

    for child in current_node.children:
        #sostituisco il parent del prec_node
        parents = child.parents
        
        for i in range(0, len(parents)):
            if parents[i].node_id == current_node.node_id:
                parents[i] = upstream_node

    #aggiorno i children del nodo upstream
    if current_node in upstream_node.children:
        upstream_node.children.remove(current_node)
    for child in current_node.children:
        if child not in upstream_node.children:
            upstream_node.children.append(child)

    #caso in cui current era il nodo root del grafo
    if graph is not None and graph.target_root.node_id == current_node.node_id:
        graph.target_root = upstream_node

    #pulisco i riferimenti
    current_node.parents.clear()
    current_node.children.clear()

    return upstream_node
    
class GraphOptimizer:
    def optimize(self, graph: ParsedGraph) -> ParsedGraph:
        changed = True
        while changed:
            changed = False

            #con |= (ior) si usa una semantica eager che non valuta la seconda parte prima di assegnare in changed.
            #così facendo per ogni iterazione si applica solo la prima regola valida.
             
            changed |= self._eliminate_identity_selects(graph)
            #possibili altre regole
        return graph

    def _collect_nodes(self, root: OpNode) -> List[OpNode]:
        """
        Raccoglie i nodi in ordine post-order (foglie prima, root alla fine).
        Utilizzato per evitare modifiche in place dei grafi che potrebbero causare bug.
        """
        visited = set()
        order = []

        def dfs(node: OpNode):
            if node.node_id in visited:
                return
            visited.add(node.node_id)
            for p in node.parents:
                dfs(p)
            order.append(node)

        dfs(root)
        return order

    def _eliminate_identity_selects(self, graph: ParsedGraph) -> bool:
        nodes = self._collect_nodes(graph.target_root)
        changed = False

        for node in nodes:
            if not node.parents or not isinstance(node, UnaryNode):
                continue

            if self._is_identity_select(node):
                remove_and_relink(node, graph)
                changed = True

        return changed
    
    def _is_identity_select(self, node: OpNode) -> bool:
        """
        Verifica se un SelectOpNode è una proiezione identità ridondante.
        
        Criteri di identità:
        1 node.schema_out coincide con parent.schema_out (stesse colonne e stessi tipi).
        2. Il numero di espressioni proiettate è pari al numero di campi dello schema.
        3. Ciascuna espressione è un COL_REF puro che non applica ridenominazioni (alias != name).
        """

        #verifica il tipo di operazione
        if not isinstance(node, SelectOpNode):
            return False

        if len(node.parents) != 1:
            return False
        parent = node.parents[0]

        #controllo schemi indipendente dall'ordine delle chiavi, funziona con la deduplicazione degli struct
        if node.schema_out != parent.schema_out:
            return False

        expressions: List[Dict[str, Any]] = node.expressions
        if expressions is None:
            raise ValueError(
                f"Nodo di select riscontrato senza espressioni durante l'ottimizzazione.\n{node.raw_dict}"
            )

        #ci sono più o meno attributi di prima
        if len(expressions) != len(parent.schema_out):
            return False

        #validazione di ogni espressione
        seen_cols: Set[str] = set()
        for expr in expressions:
            #solo trasposizioni di colonne
            if expr.get("expr_type") != ExprType.COL_REF:
                return False

            #colonne che non c'erano prima
            source_col = expr.get("name")
            if not source_col or source_col not in parent.schema_out:
                return False

            #ridenominazioni
            target_col = expr.get("alias") or source_col
            if target_col != source_col:
                return False

            seen_cols.add(source_col)

        #guarda se sono state coperte tutte le colonne
        return seen_cols == set(parent.schema_out.keys())


    