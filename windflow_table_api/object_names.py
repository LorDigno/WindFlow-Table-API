from enum import Enum

class OpType(str, Enum):
    """
    Rappresenta tutti i tipi di operatori supportati nella Table API di WindFlow.
    Usata trasversalmente tra api, codegen e runtime per disaccoppiare il dispatch
    dalle stringhe cablate.
    """

    #sorgenti e riferimenti
    TABLE_REF = "TAB_REF"
    FROM = "FROM"
    SINK = "SINK"

    #operatori unari semplici
    WHERE = "WHERE"
    SELECT = "SELECT"
    DISTINCT = "DISTINCT"

    #raggruppamennti
    GROUP_BY = "GROUP_BY" #globale
    WINDOW_GROUP_BY = "WINDOW_GROUP_BY"

    #congiunzioni   
    JOIN_INTERVAL = "JOIN_INTERVAL"
    JOIN_WINDOW = "JOIN_WINDOW"

    #operatori insiemistici
    UNION = "UNION"
    UNION_ALL = "UNION_ALL"
    INTERSECT = "INTERSECT"
    INTERSECT_ALL = "INTERSECT_ALL"

    def __str__(self) -> str:
        return self.value

    @property
    def is_set_op(self) -> bool:
        """Restituisce True se l'operatore appartiene alla famiglia insiemistica."""
        return self in SET_OPERATIONS

SET_OPERATIONS = frozenset({
        OpType.UNION,
        OpType.UNION_ALL,
        OpType.INTERSECT,
        OpType.INTERSECT_ALL,
    })