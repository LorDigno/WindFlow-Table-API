==**Architettura e Moduli**==
Il package si chiama windflow_table_api ed è diviso in tre sotto-package api, codegen e runtime. 
Il sotto-package api è quello con cui interagisce l'utente e ha come obbiettivo quello di creare un file JSON che rappresenti le query da fare.
Il sotto-package codegen esegue il parsing del JSON e genera del codice C++ che con l'uso dei builder custom per le operazioni della TableAPI istanzia la query a livello di WindFlow nativo.
Il sotto-package runtime gestisce la compilazione ed esecuzione del codice generato.

A tempo di scrittura solo api è stato scritto ed è quasi completo.

Dunque vediamo i moduli interni di API:
```
api/
	__init__.py
	datatypes.py       #contine un'enum per i tipi supportati (Py->C++)
	draft.py           #la classe draft usata per comporre operatori
	durations.py       #classi varie utilizzate per gestire il tempo
	expressions.py     #classi e helper per fare le espressioni utente
	operators.py       #classi che rappresentano gli operatori logici
	schema.py          #classi per gestire gli schemi dei dati
	table_env.py       #registra le tabelle e crea il JSON 
	table.py           #classi Table e Query che offrono i metodi fluent
	windows.py         #classi di rappresentazione di finestre ed intervalli
```

C'è molto da dire su vari di questi moduli quindi ci sarà una sezione per molti di loro.
A tempo di scrittura sono tutti "completi" tralasciando la rappresentazione in JSON e table_env.py a cui manca il metodo .execute(query), il cui scopo è appunto esplorare le varie Table e fare il JSON.
# Sotto-package Api
Si presuppone che ci sia stato un import di tipo:
```
import windflow_table_api as wf

oppure 

from windflow_table_api import *
```

Personalmente userò una sintassi in accordo col secondo import per evitare di scrivere wf ovunque.
## 1.0 Introduzione
Mi sembra intuitivo partire dalla classe che l'utente utilizzerò più spesso ovvero Table.
Una Table è caratterizzata dal proprio table_id e il proprio Schema.
Lo Schema è una rappresentazione della struttura dei dati di una tabella simile ad un dizionario o uno struct.

Per creare una tabella sorgente nuova bisogna chiamare l'apposito metodo dell'ambiente passandogli il filepath, lo schema, un possibile nome e una possibile colonna temporale.
(si approfondirà più avanti).

Lo Schema si può creare tramite lo SchemaBuilder. 

```
env = TableEnvironment()

#questo sarà l'esempio ricorrente
sensor_schema = (SchemaBuilder()
	.add_column("sensor_id", DataTypes.STRING)
	.add_column("temperature", DataTypes.DOUBLE)
	.add_column("humidity", DataTypes.DOUBLE)
	.build()
)

tab = env.table_from_file("sensor_input.csv", sensor_schema, "sensor_source")
```

Le tabelle sono poi gli oggetti che permettono all'utente di formulare query tramite l'invocazione di metodi che creano gli operatori corrispondenti.

```
q = (tab
	.where(col("temperature") > 30)
	.select("sensor_id", "temperature")
)
```

Le Query sono una specializzazione delle Table che rappresentano flussi derivati. 
Infine tramite l'ambiente si può eseguire una Query, questo vuol dire rappresentare tutti gli operatori usati per arrivare alla Query finale in JSON.

```
env.execute(q)

#output atteso nel file json
{
    "query_id": "sensor_source_query_2",
    "root": {
        "op_type": "SELECT",
        "expressions": [
            {
                "expr_type": "COL_REF",
                "name": "sensor_id",
                "data_type": "STRING"
            },
            {
                "expr_type": "COL_REF",
                "name": "temperature",
                "data_type": "DOUBLE"
            }
        ],
        "schema_in": {
            "sensor_id": "STRING",
            "temperature": "DOUBLE",
            "humidity": "DOUBLE"
        },
        "schema_out": {
            "sensor_id": "STRING",
            "temperature": "DOUBLE"
        },
        "parents": [
            {
                "op_type": "WHERE",
                "condition": {
                    "expr_type": "BINARY_OP",
                    "op": ">",
                    "data_type": "BOOLEAN",
                    "left": {
                        "expr_type": "COL_REF",
                        "name": "temperature",
                        "data_type": "DOUBLE"
                    },
                    "right": {
                        "expr_type": "LITERAL",
                        "value": 30,
                        "data_type": "INT"
                    }
                },
                "schema_out": {
                    "sensor_id": "STRING",
                    "temperature": "DOUBLE",
                    "humidity": "DOUBLE"
                },
                "schema_in": {
                    "sensor_id": "STRING",
                    "temperature": "DOUBLE",
                    "humidity": "DOUBLE"
                },
                "parents": [
                    {
                        "op_type": "FROM",
                        "source_id": "sensor_source",
                        "schema_out": {
                            "sensor_id": "STRING",
                            "temperature": "DOUBLE",
                            "humidity": "DOUBLE"
                        },
                        "file_path": "sensor_input.csv",
                        "time_col": null
                    }
                ]
            }
        ]
    }
}

```

Questo era per dare un'idea generale d'uso dell'API, ora vediamo le varie componenti.
## 2.0 Schema e DataTypes
Moduli il cui scopo è rappresentare rispettivamente la struttura e il tipo dei valori dei dati.
#### 2.1 DataTypes
Come detto precedentemente lo schema rappresenta la struttura dei dati, questi ovviamente sono tipizzati solo che traducendo alla fine tutto in C++ serve una conversione esplicita, questo è il ruolo di DataTypes.

```
class DataTypes(Enum):
    """
    Rappresenta i tipi di dato supportati dalla Table API.
    Mappa i nomi logici della Table API sui reali tipi C++ nativi di WindFlow.
    """

    STRING = ("std::string", "STRING")
    INT = ("int32_t", "INT")
    BIGINT = ("int64_t", "BIGINT")
    FLOAT = ("float", "FLOAT")
    DOUBLE = ("double", "DOUBLE")
    BOOLEAN = ("bool", "BOOLEAN")

    def __init__(self, cpp_type: str, logical_name: str):
        self.cpp_type = cpp_type
        self.logical_name = logical_name
```
Possibili aggiunte in futuro.
Da notare come non ci siano le unità di tempo, quelle vengono gestite nel modulo durations.
#### 2.2 SchemaBuilder e Field
Creare uno Schema come visto nell'esempio iniziale è permesso tramite SchemaBuilder con i metodi appositi ma è anche possibile passando un dizionario ben formattato.

```
class SchemaBuilder:
    """Builder fluente per la costruzione di uno Schema. """
    
    def __init__(self):
        self._fields: Dict[str, Field] = {}
        
    def build(self) -> Schema:
        """Finalizza lo schema costruito e lo rende."""
        return Schema(self._fields)
        
    #e vari altri    
```

Il metodo principale per quanto riguarda l'utente è add_column che aggiunge allo stato interno dello SchemaBuilder una nuova colonna .

```
def add_column(
        self, name: str, data_type: DataTypes, 
        expression: Optional[Expression] = None
    ) -> SchemaBuilder:
        """
        Aggiunge una colonna specificando esplicitamente nome, 
        DataType ed eventuale espressione.
        Se la colonna è già presente solleva un errore.
        """
        #body
```

Le colonne sono rappresentate via oggetti Field che racchiudono il nome, il tipo e una possibile espressione associata.

```
class Field:
    """
    Rappresenta un singolo campo/colonna all'interno di uno Schema.
    Mantiene il nome logico, il DataType e l'eventuale Expression che l'ha generato.
    """
    
    def __init__(
	    self, name: str, data_type: DataTypes, 
	    expression: Optional[Expression] = None
	):
        self.name = name
        self.data_type = data_type
        self.expression = expression
```

E' presto per parla di espressioni ma alcuni Field hanno bisogno di mantenersi l'espressione che la colonna deve rappresentare.

```
q = tab.select(col("temperature") + 42)   #si deve ricordare di fare + 42
```

Per aggiungere espressioni allo schema, in SchemaBuilder, c'è anche il metodo esplicito add_expression che ricava il nome dall'alias dell'espressione stessa e il tipo dall'applicazione con lo schema corrente.
Altrimenti si può passere l'espressione come ultimo parametro di add_column.

```
def add_expression(
            self, expr: Expression,
            input_schema: Schema,
            default_name: Optional[bool] = False
        ) -> SchemaBuilder:
        """
        Aggiunge una colonna derivata direttamente da un'Expression:
        - Estrae il nome dall'alias o dal nome di default dell'espressione 
          (se default_name = True prende sempre il default)
        - Calcola il DataType applicando l'espressione sullo schema di input
        - Associa l'oggetto Expression al campo

        """
        #body
        #chiama add_column e passa l'espressione con i dati ricavati da essa
```

```
#un modo per ottenere lo schema della query precedente
expr = col("temperature") + 42

selected_schema = (SchemaBuilder()
	.add_expression(expr, tab.schema)
	.build()
)
```

Il metodo build non fa altro che inizializzare e rendere lo schema costruito internamente.
#### 2.3 Schema
Una volta costruito uno schema è immutabile.

```
def __init__(self, fields: Dict[str, Field]):
        self._fields: Dict[str, Field] = fields.copy()
```

Durante la composizione di una Query lo schema viene calcolato dinamicamente ad ogni passo, senza modificare quello della Table attuale, quindi l'utente deve inserire solo quello della sorgente iniziale.

```
q = tab.select("sensor_id", "humidity")
#q ha schema {"sensor_id": STRING, "humidity: DOUBLE"}
#lo schema di tab rimane invariato
```

La classe Schema stessa offre vari metodi generalmente usati internamente ma utili a scopo di debugging.

```
@property
def fields(self) -> Dict[str, DataTypes]:
        """Restituisce una mappa nome_colonna -> DataType""
        #body

def get_columns(self) -> List[str]:
        """Restituisce la lista dei nomi delle colonne."""
        #body
        
def get_types(self) -> List[DataTypes]:
        """Restituisce la lista ordinata dei DataType delle colonne."""
        #body

def has_field(self, name: str) -> bool:
        """Controlla che la colonna [name] sia presente nello Schema"""
        #body

def get_field(self, column_name: str) -> Field:
        """
        Restituisce l'oggetto Field associato alla colonna.
        Solleva un'eccezione se tale colonna non è presente nello Schema.
        """
        #body

def get_type_for(self, column_name: str) -> DataTypes:
        """
        Restituisce il DataType di una specifica colonna.
        Solleva un'eccezione se tale colonna non è presente nello Schema.
        """
        #body
        
def get_expression_for(self, column_name: str) -> Optional[Expression]:
        """
		Restituisce l'espressione associata a una colonna se presente.
		Solleva un'eccezione se tale colonna non è presente nello Schema.
        """
        #body
```

Infine due schemi si reputano equivalenti se contengono gli stessi Field associati agli stessi nomi, a prescindere dall'ordine d'inserimento.

```
def __eq__(self, other) -> bool:
	if not isinstance(other, Schema):
	    return False
    return other.fields == self.fields
```
## 3.0 Table e Draft
Modulo chiave dell'API utilizzato dall'utente per formulare query. 
E' composto da due classi principali Table e Query, la seconda è una specializzazione della prima che contiene gli operatori necessari a calcolarla a partire dalla tabella madre.

Le Table sorgente vanno create esplicitamente via l'ambiente mentre le Query vengono inizializzate (sempre tramite l'ambiente) in automatico a seguito di una select. 
#### 3.1 Stato di Table
Come detto in introduzione una Table è definita dal proprio table_id e il proprio Schema ma ci sono altre informazioni da mantenere, come a che ambiente appartiene.

La tabella madre che è la Table su cui è stata eseguita una query per ottenere quella attuale.
Le Query hanno per forza una tabella madre mentre le Table sorgente no.

```
    def __init__(
        self,
        schema: Schema,
        table_id: str,
        env: TableEnvironment,
        parent_table: Optional[str] = None,
    ) -> None:
        """
        Inizializza una Table con lo schema di input, id univoco e riferimento all'ambiente.
        """
        self._schema = schema
        self._table_id = table_id
        self._env = env
        self._parent_table = parent_table
        
        #necessari alla creazione delle Query, vedremo dopo
        self._draft: Optional[Draft] = None
        self._draft_name: Optional[str] = None
```

Il costruttore esplicito di Table e Query non dovrebbe mai essere chiamato, l'ambiente esiste appositamente per gestire la loro creazione. 
Il table_id può essere specificato dall'utente alla creazione tramite l'ambiente, in caso contrario è generato automaticamente.

```
tab1 = env.table_from_file(filepath, schema)
#table id automatico: "source_stream_file_1"
```

I campi schema, table_id ed env che sono privati sono ottenibili tramite property.

```
	@property
    def schema(self) -> Schema:
        """Restituisce lo Schema corrente della tabella."""
        return self._schema
  
    @property
    def table_id(self) -> str:
        """Restituisce l'identificativo univoco della tabella assegnato dall'ambiente o custom."""
        return self._table_id

    @property
    def env(self) -> TableEnvironment:
        """Restituisce il riferimento al TableEnvironment di appartenenza."""
        return self._env 
```

#### 3.2 Fase di Drafting
Come si vede nel costruttore ci sono anche dei campi il cui scopo è gestire il drafting di una Query in costruzione. 
L'oggetto Draft (classe presente nell'omonimo modulo) è quello che tiene traccia degli operatori applicati ad una Table e verrà poi utilizzato per istanziare la Query.

L'idea è che durante la composizione di una nuova Query lo stato della Table non debba cambiare quindi tutte le informazioni sono tenute nel Draft.
Sono solo i metodi di select a rendere la nuova Query quindi in teoria si può dividere l'applicazione di operatori fra più righe di codice.

```
tab.where(col("temperature") < 10)         
#draft: [TabRef, Where]

tab.group_by("sensor_id")
#draft [TabRef, Where, GroupBy]

q = tab.select("sensor_id", avg("temperature"))
#draft: [TabRef, Where, GroupBy, Select]
#viene creata la Query e pulito il draft

tab.get_draft()
#draft: []
```

Tutti i vari metodi di applicazione di un operatore internamente aggiornano il Draft in modo automatico, difatti tutto questo dovrebbe essere trasparente all'utente.
Il ogni caso Table offre dei metodi per controllare il Draft utilizzati internamente ma anche pensati per facilitare il debugging.

```
def is_drafting(self) -> bool:
	"""Verifica se la tabella ha una catena di operatori in fase di costruzione."""
	return self._draft != None

def get_draft(self) -> Draft:
    """
    Restituisce il Draft corrente.
    Se non esiste ne crea uno nuovo vuoto.
    """
    #body  

def clear_draft(self) -> None:
        """Azzera lo stato del Draft interno."""
        self._draft = None
        self._draft_name = None
  
def name_draft(self, name: str) -> None:
        """
        Assegna il nome al prossimo Draft che sarà 
        il table_id della query risultante.
        Non si può chiamare durante il drafting ma solo prima.
        """
        #body
```
#### 3.3 Funzionamento Interno di Draft
Come già detto il Daft vuole essere trasparente all'utente ma capirne il funzionamento è necessario per vedere i metodi degli operatori in Table.

```
class Draft:
    """
    Rappresenta lo stato temporaneo di composizione di una query su una Table.
    Accumula gli operatori intermedi prima della finalizzazione tramite select().
    """
  
    def __init__(
            self,
            source_table_id: str,
            source_table_schema: Schema,
            custom_name: Optional[str] = None):
        """
        Crea il Draft vuoto con nome se specificato tramite un precedente table.name_draft(nome).
        """

        self.source_table_id = source_table_id
        self.source_table_schema = source_table_schema
        self.custom_name = custom_name
        self._operators: List[Operator] = []
```

Nel pratico gli operatori vengono tenuti in una lista ordinata ma ognuno di essi avrà anche il puntatore all'oggetto Operator che lo precede logicamente.

Durante la formulazione di una query si da per scontato che l'operatore logicamente precedente a quello appena creato sia l'ultimo che è stato aggiunto al Draft. 
Questo non permette di avere "biforcazioni" del flusso fra un operatore e l'altro.

Quando viene inserito il primo operatore nel Draft il suo predecessore sarà un TableRefOp che rappresenta la tabella madre.

```
#metodo generalmente usato per inserire l'operatore precedente
def get_last_operator(self) -> Operator:
	"""
    Restituisce l'ultimo operatore attualmente presente nel Draft.
    Se non ci sono operatori rende il TableRefOp alla tabella madre.
    """
    #body
```

```
tab.where(cond)
#lista: [TableRef, Wehre]
#grafo logico: where.parent -> table_ref.parent -> None
```

Il TableRefOp servirà all'ambiente a capire cosa inserire a monte. 
Se si riferisce ad una Query ci sarà una chiamata ricorsiva ad execute e un collegamento con l'ultimo operatore di select.
Se si riferisce ad una Table sorgente allora viene inserito un operatore di From.

Si hanno dunque i seguenti metodi per inserire operatori nel Draft.
```
def add_unary_operator(self, operator: UnaryOperator) -> None:
        """Collega il nuovo operatore unario all'ultimo inserito nel Draft."""
  
		#controlli vari di validità ....
  
        prev_op = self.get_last_operator()
        operator.set_parents([prev_op])    
        self._operators.append(operator)
        
def add_binary_operator(
        self,
        operator: BinaryOperator,
        right_parent: TableRefOp,
    ) -> None:
        """
        Collega il nuovo operatore binario all'ultimo inserito nel Draft.
        Il parent destro deve essere un TableRefOp.
        """
  
		#controlli vari di validità ....
  
        left_op = self.get_last_operator()
        operator.set_parents([left_op, right_parent])
        self._operators.append(operator)
```

Da notare come gli operatori binari possono ricevere in input come genitore destro solo un TableRefOp.

```
sub_q = (tab
	.where(col("temperature") > 30)
	.select("sensor_id","temperature"
)
q = (tab
	.where(col"temperature" < 10)
	.union(sub_q)
	.select("sensor_id", "temperature"
)
#il TableRefOp viene creato dentro union a partire da sub_q
```

Un altro appunto da fare sul funzionamento interno di Draft è che ogni operatore mantiene i propri schemi di input ed output che non sono per forza uguali.
Di conseguenza alla creazione di un nuovo operatore lo schema di input deve corrispondere allo schema di output del precedente.

```
	@property
    def current_schema(self) -> Schema:
        """
        Restituisce lo schema di output dell'ultimo operatore inserito nel Draft, 
        ovvero
        lo schema che riceverà in input il prossimo operatore inserito.
        """

        return self.get_last_operator().schema_out
```

```
q = (tab
	.where(cond)           #in input ed output lo schema di tab
	.join(tab2, "key")     #in input lo schema di tab, in output il join
	.select("key", ...)    #in input lo schema di join, in output la selezione
)
```

Per via di alcune restrizioni sintattiche dovute allo schema per ora il Draft bloccherà l'inserimento di un qualsiasi operatore a seguito di un group_by che non sia una select.
Questo è necessario perché solo nella select si scopre quali aggregazioni dovrà calcolare effettivamente il group_by.
Se si vuole comprenderne meglio i dettagli c'è una sezione apposita in questa stessa documentazione.
#### 3.4 Metodi di Operazioni in Table
I vari metodi in Table seguono tutti lo stesso schema concettuale in cui si crea l'oggetto Operator desiderato e poi s'inserisce nel Draft con i metodi appositi.

```
#esempio col where
def where(self, condition: Expression) -> Table:
        """
        Applica un predicato booleano per filtrare i record dello stream.
        Il predicato deve essere un'Expression.
        """
  
        draft = self.get_draft()
        where_op = WhereOp(condition, draft.current_schema)
        draft.add_unary_operator(where_op)
  
        return self
        #per poter concatenare metodi inline
```

Gli eventuali controlli sulla correttezza dell'input possono essere fatti sia nel metodo in Table che nel costruttore dell'oggetto Operator..

Gli operatori di modifica allo schema come drop_columns o rename_columns sono internamente implementati tramite un oggetto SelectOp e chiamano al loro interno il metodo select. 

```
#esempio con add_columns
def add_columns(self, *expressions: Expression) -> Query:
        """
        Calcola e aggiunge una o più colonne allo schema 
        esistente per creare un nuova Query.
        Implementato tramite un operatore di select.
	    Si consiglia di dare un alias alle espressioni di input.
        """
        selections = #colonne attuali più quelle nuove

        return self.select(*selections)
```

L'operatore di select finalizza la Query ricavata dal Draft invocando il metodo apposito dell'ambiente in cui è presente la tabella attuale.

```
def select(self, 
	*columns: Union[str, Expression],
	distinct: bool = False
	) -> Query:
        """
        Proietta o calcola nuove colonne a partire da nomi o espressioni.
        Finalizza la nuova Query nell'ambiente e la rende.
        Con distinct = True aggiunge un operatori di Distinct a seguito della selezione.
        """
        
        #crea ed inserisce gli operatori

        q = self.env.create_query(
            draft.current_schema,
            self._table_id,
            draft.get_last_operator(),
            draft.custom_name
        )
  
        self.clear_draft()
        return q
```

Come accennato precedentemente gli operatori binari richiedo che il parametro che indica la seconda tabella sia un oggetto Table propriamente detto.
Si possono anche fare subquery purché ci sia una select a rendere l'effettivo oggetto Query altrimenti per via della semantica a Draft viene considerata la tabella madre.

```
tab.join(
	tab2.where() ,   #non avendo chiuso la query conta solo tab2
	"key")
	
tab.join(
	tab2.where(cond).select(...),
	"key"
)	

#oppure se ho definito q in anticipo
tab.join(q, "key")
```

Il metodo join può anche prendere in input una Window o un Interval se non si vuole fare la InnerJoin di default. 
Il metodo group_by in modo simile può accettare una Window.

```
tab.join(tab2, "key", interval)
```

Gli operatori insiemistici come Union e Intersect hanno tutti dei metodi appositi ma per via della loro somiglianza nei controlli vengono implementati dallo stesso metodo _apply_set_op_. 
Questa cosa è presente anche al livello di Operator in cui ognuno di loro è un SetOp con un identificativo diverso.

```
#esempio con la intersect_all
   def intersect_all(self, other: Table) -> Table:
        """
        Calcola l'intersezione tra le tuple di due 
        stream con semantica da multinsieme.
        Stato potenzialmente infinito in base al numero di tuple uniche.
        """

        return self._apply_set_op(other, SetOpType.INTERSECT_ALL)
```

## 4.0 Operators
Questo modulo dovrebbe essere completamente trasparente all'utente finale che ci interagisce solo tramite i metodi di Table.
Comunque nel caso servisse controllare i Draft o il file JSON finale questa sezione spiega come funziona senza andare nel dettaglio su ogni tipo di operatore.

Gli oggetti Operator raccolgono le informazioni necessarie successivamente ad eseguire le operazioni richieste.
Dato che non ci sono vere e proprie elaborazioni di dati al livello di Python non hanno metodi che implementano l'operazione in sé ma si limitano a controllare l'input ricevuto e, se necessario , inferire lo schema di output.
#### 4.1 Classe Operator
Nel modulo operators.py sono presenti tre classi astratte Operator, UnaryOperator e BinaryOperator.

La classe Operator è la radice della gerarchia delle classi e sancisce lo stato minimo che ogni operatore deve mantenere:
- schema_out: lo schema di output.
- input_schema: lo schema di input.
- parents: la lista degli operatori che confluiscono nel corrente.
A questi attributi ci si può accedere tramite @property.

```
class Operator(ABC):  
	"""
    Classe base astratta per tutti i nodi logici degli operatori di WindFlow.
    Rappresenta un'operazione sullo stream che riceve uno o più schemi in input
    e produce uno schema in output.
    Lo schema di output viene generalmente calcolato dinamicamente in base alla query.
    """
  
    def __init__(
        self,
        schema_out: Schema,
        input_schema: Schema,
        parents: Optional[List[Operator]] = None
    ) -> None:
        self._schema_out = schema_out
        self._input_schema = input_schema
        self._parents: List[Operator] = parents if parents is not None else []
```

Ci sono vari metodi astratti che le classi concrete dovranno implementare.

```
	@abstractmethod
    def set_parents(self, parents: List[Operator]) -> None:
        """Imposta/sovrascrive la lista degli operatori parent."""
        pass
        
    @abstractmethod
    def get_op_type(self) -> str:
        """Restituisce l'identificativo univoco del tipo di operatore."""
        pass
  
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializza l'operatore e la sua configurazione in un dizionario
        utilizzato per la generazione del JSON.
        """
        pass
```

Il metodo to_dict non è presente solo negli operatori ma in quasi ogni classe presente nell'API. 
Per creare il JSON verrà utilizzata la mappatura dei dizionari nativi Python quindi tutto ciò che va rappresentato verrà prima serializzato in dizionario.
I dizionari degli operatori e delle espressioni utente di solito sono i più numerosi nei JSON finali.
#### 4.2 Operatori Unari
Gli operatori unari sono quelli con un solo genitore e che estendono UnaryOperator.

```
class UnaryOperator(Operator, ABC):
    """
    Classe base per operatori a singolo ingresso come Filter, Select, GroupBy.
    """
  
    def __init__(self,
                schema_out: Schema,
                input_schema: Schema,
                parent: Optional[Operator] = None
        ) -> None:
        parents = [parent] if parent is not None else []
        super().__init__(schema_out=schema_out, 
				        input_schema=input_schema, parents=parents)
  
    @property
    def parent(self) -> Optional[Operator]:
        """Restituisce l'unico operatore parent se presente."""
        return self._parents[0] if self._parents else None
  
    def set_parents(self, parents: List[Operator]) -> None:
        """
        Imposta/sovrascrive la lista degli operatori parent.
        Se passata una lista di più di un operatore solleva un errore.
        """
        #body
```

Come visto nella sezione su 3, gli operatori vengono creati nei metodi di Table mentre i genitori vengono assegnati dal Draft per questo il campo "parent" è opzionale.

Gli operatori unari sono SelectOp, WhereOp, GroupByOp e DistinctOp.

```
class SelectOp(UnaryOperator):
    """
    Rappresenta l'operatore di proiezione e i vari 
    operatori di modifica allo schema.
    Costruisce un nuovo Schema di output inferendo nomi e 
    tipi di dato da ciascuna Expression fornita.
    """
    #body
    
 class WhereOp(UnaryOperator):
    """
    Rappresenta un operatore di filtraggio basato su una condizione booleana.
    Filtra gli elementi in ingresso senza alterare lo schema dello stream.
    """
    #body   
    
class GroupByOp(UnaryOperator):
    """
    Classe che rappresenta l'operatore di GroupBy.
    L'operatore TableAPI mantiene lo stesso schema ricevuto in input 
    ma nel JSON per l'istanziazione WF avrà uno schema di output 
    definito in base alle aggregazioni della select.
    """
    
 class DistinctOp(UnaryOperator):
    """
    Rappresenta l'operatore di distinzione sullo stream corrente.
    """   
```

Di questi WhereOp, DistinctOp e GroupByOp mantengono in output lo stesso stato che in input.
Il group_by però è strutturato così solo temporaneamente, durante il drafting il suo schema sarà deciso dalla select che lo segue (che ha le aggregazioni).
Proprio per questo non ci possono essere operatori fra il group_by e la select di una query. 
Per ulteriori dettagli consultare la sezione apposita.
#### 4.3 Operatori Binari 
Gli operatori binari estendono BinaryOperator e hanno una coppia di genitori.

```
class BinaryOperator(Operator, ABC):
    """
    Classe base per operatori a doppio ingresso come Join, Union e Intersect.
    """
  
    def __init__(
        self,
        schema_out: Schema,
        input_schema: Schema,
        left_parent: Optional[Operator] = None,
        right_parent: Optional[Operator] = None,
    ) -> None:
        parents = []
        if left_parent:
            parents.append(left_parent)
        if right_parent:
            parents.append(right_parent)
        super().__init__(schema_out=schema_out, 
					     input_schema=input_schema, 
					     parents=parents)

    @property
    def left_parent(self) -> Optional[Operator]:
        return self._parents[0] if len(self._parents) > 0 else None
  
    @property
    def right_parent(self) -> Optional[Operator]:
        return self._parents[1] if len(self._parents) > 1 else None

    def set_parents(self, parents: List[Operator]) -> None:
        """
        Imposta/sovrascrive la lista degli operatori parent.
        Se passata una lista senza esattamente due operatori solleva un errore.
        Il primo diventa il left_parent e il secondo il right_parent.
        """
        #body
```

Gli operatori binari sono JoinOp e SetOp. 

A seconda della presenza o meno di un Interval o di una Window il JoinOp rappresenta uno dei tre metodi di Join presenti a livello di WindFlow.
Quello di default è la InnerJoin che non richiede il passaggio di un attachment.

```
class JoinOp(BinaryOperator):
    """
    Classe che rappresenta gli operatori di Inner/Interval/Windowed Join 
    in base ai parametri dati.
    """
  
    def __init__(
        self,
        key: str,
        tab1_schema: Schema,
        tab2_schema: Schema,
        attachment: Optional[Union[Window, Interval]]
    ) -> None:
    #body
```

SetOp implementa tutte le operazioni insiemistiche che hanno stato e schema uguale fra loro anche se l'operazione in sé è diversa.

```
class SetOpType(Enum):
    UNION = "UNION"
    UNION_ALL = "UNION_ALL"
    INTERSECT = "INTERSECT"
    INTERSECT_ALL = "INTERSECT_ALL"
    
class SetOp(BinaryOperator):
	"""
    Classe che rappresenta gli operatori insiemistici 
    Union/UnionAll/Intersect/IntersectAll.
    """
  
    def __init__(
        self,
        set_op_type:SetOpType,
        tab1_schema: Schema,
        tab2_schema: Schema
    ) -> None:   
    #body 
```

#### 4.4 Operatori senza genitori
Gli unici due operatori senza genitori sono TableRefOp e FromOp, in entrambi il metodo set_parents lancia un'eccezione. 

Il TableRefOp indica all'ambiente che in quel punto arrivano tuple derivanti da un'altra Table, a livello di C++ serve a capire dove collegare due topologie di query diverse.
Spesso viene usato per definire l'origine della Query dalla tabella madre ma è presente anche come secondo genitore negli operatori binari.

Dato che non si hanno genitori di alcun tipo lo schema di input è inizializzato allo schema vuoto, non che serva a molto dato che nella rappresentazione JSON non è presente. 

```
class TableRefOp(Operator):
    """
    Operatore foglia senza parents.
    Rappresenta un'altra tabella a da cui arrivano dati.
    """
  
    def __init__(
        self,
        source_table_id: str,
        schema_out: Schema,
    ) -> None:
        super().__init__(schema_out=schema_out,
				         input_schema=SchemaBuilder().build(), 
				         parents=[])
        self.source_table_id = source_table_id
        
    #body    
```

Il FromOp non è mai presente nel Draft che inserisce di default solo TableRefOp bensì viene inserito durante la execute dall'ambiente quando viene trovato un TableRefOp che si riferisce ad una tabella sorgente.

```
class FromOp(Operator):
    """
    Operatore foglia senza parents.
    Rappresenta l'origine dei dati (sorgente o tabella madre).
    """
  
    def __init__(
        self, source_table_id: str,
        schema_out: Schema,
        time_col: Optional[TimeCol] = None,
        file_path: Optional[str] = None
    ) -> None:
        super().__init__(schema_out=schema_out,
				         input_schema=SchemaBuilder().build(),
				         parents=[])

        self.source_table_id = source_table_id
        self.time_col = time_col  
        self.file_path = file_path
        
   #body
```
## 5.0 Expressions
Le espressioni utente sono utilizzate per formulare condizioni, funzioni d'aggregazione e selezioni personalizzabili dall'utente.

Queste estendono tutte la classe astratta Expression e vengono spesso create implicitamente o tramite l'uso di funzioni helper, è sconsigliato l'utilizzo dei costruttori espliciti.
#### 5.1 Expression
La base per tutte l'espressioni, contiene l'overloading dei metodi magici dei vari operatori di Python per permettere una sintassi chiara, la logica degli alias e alcuni metodi astratti.

```
	@abstractmethod
    def get_type(self, schema: Schema) -> DataTypes:
        """
        Calcola e restituisce il DataType risultante applicando
        l'espressione sullo schema di input.
        """
        pass
  
    @abstractmethod
    def to_dict(self, applied_schema: Schema) -> Dict[str, Any]:
        pass
  
#metodi necessari per i raggruppamenti
    @abstractmethod
    def validate_grouped(self, keys: List[str]) -> bool:
        """
        Controlla che questa espressione possa essere selezionata a 
        seguito di un group_by(keys).
        """
        pass
        
    @abstractmethod
    def aggregation_dependencies(self) -> List[AggregateExpression]:
        """
        Rende le aggregazioni che è necessario calcolare per 
        valutare l'espressione.
        """
        pass
        
	@abstractmethod
    def rewrite_grouped(self) -> "Expression":
        """Riscrive l'espressione affinché faccia riferimento ai 
        campi generati dallo schema del GroupByOp."""
        pass    
```

Il metodo get_type è vitale per garantire la correttezza di tipo delle varie espressioni composte. 
I metodi per il raggruppamento verranno spiegati nella sezione 6 sul group_by.
Se gli input sono sbagliati solleva un'eccezione di tipo.
##### 5.1.1 Metodi Magici
In Python si può fare, nelle classi, l'overloading degli operatori di base come "+", "/" e ">".
Sfruttando questa peculiarità del linguaggio purché il primo operando è dichiarato esplicitamente come un'espressione si semplifica la sintassi richiesta dall'API.

```
expr = col("temperature") / 100
#equivale a un ipotetico: 
expr = col("temperature").div(lit(100, DataTypes.INT)) 

#con più operandi si consiglia di dividere a blocchi
cond = (
    (col("humidity") > 20) &         #& che è l'and bit a bit di python
    (col("temperature") > 20) &      #qua è l'and logico
    (col("temperature") < 30)
)

print(cond)
#output atteso:
(((col('humidity') > lit(20: INT)) && (col('temperature') > lit(20: INT))) && (col('temperature') < lit(30: INT)))

print(cond.to_dict(sensor_schema))
#output atteso:
{
	'expr_type': 'BINARY_OP', 
	'op': '&&', 'data_type': 'BOOLEAN', 
	'left': {
		'expr_type': 'BINARY_OP', 
		'op': '&&', 'data_type': 'BOOLEAN', 
		'left': {
			'expr_type': 'BINARY_OP', 
			'op': '>', 'data_type': 'BOOLEAN', 
			'left': {
				'expr_type': 'COL_REF',
				'name': 'humidity', 
				'data_type': 'DOUBLE'
			}, 
			'right': {
				'expr_type': 'LITERAL', 
				'value': 20, 
				'data_type': 'INT'
			}
		}, 
		'right': {
			'expr_type': 'BINARY_OP', 
			'op': '>', 
			'data_type': 'BOOLEAN', 
			'left': {
				'expr_type': 'COL_REF', 
				'name': 'temperature', 
				'data_type': 'DOUBLE'
			}, 
			'right': {
				'expr_type': 'LITERAL', 
				'value': 20, 
				'data_type': 'INT'
			}
		}
	}, 
	'right': {
		'expr_type': 'BINARY_OP', 
		'op': '<', 
		'data_type': 'BOOLEAN', 
		'left': {
			'expr_type': 'COL_REF', 
			'name': 'temperature', 
			'data_type': 'DOUBLE'
		}, 
		'right': {
			'expr_type': 'LITERAL', 
			'value': 30, 
			'data_type': 'INT'
		}
	}
}
```

I metodi magici sono i principali istanziatori di BinaryOpExpression ognuno per il proprio operatore.

Quelli attualmente supportati sono i seguenti:
- Aritmetica: "+", "-", "/", * .
- Confronti: `==`, ">", "<", ">=", "<=", "!=".
- Logica: "&" e "|" questi sono i simboli degli operatori di and/or bit a bit che sono gli unici sovrascrivibili.

Per garantire che l'espressioni create dall'utente con questi operatori si usa il metodo get_type che lancia eccezioni in caso di tipi incompatibili.

Per permettere una notazione più snella sul secondo operando viene chiamato un metodo che cerca di convertirlo automaticamente in espressione.

```
def _to_expr(self, other: Any) -> "Expression":
        """Converte un valore scalare in una LiteralExpression se necessario."""
        
        if isinstance(other, Expression):
            return other
        return lit(other)
        
#esempio sulla somma
def __add__(self, other: Any) -> "BinaryOpExpression":
        return BinaryOpExpression(self, "+", self._to_expr(other))
```

Vedremo poi che LiteralExpression, costruita tramite "lit", può inferire alcuni dei tipi base di Python.
##### 5.1.2 Gestione degli Alias
L'unico attributo che ha la classe Expression è quello per contenere il proprio nome ed è inizializzato a None.

```
class Expression(ABC):
    """
    Classe base per qualsiasi espressione della Table API.
    """
  
    def __init__(self):
        self._alias_name: Optional[str] = None
```

Il nome è necessario per le selezioni in cui viene inserita una nuova colonna derivante da un'espressione come in add_columns o a mano in una select.

```
q = tab.select(col("temperature") + 10)

#schemi della select:
"schema_in": {
            "sensor_id": "STRING",
            "temperature": "DOUBLE",
            "humidity": "DOUBLE"
        }
"schema_out": {
            "(temperature + 10)": "DOUBLE"
        }
```

Se il nome non viene mai inizializzato l'espressione verrà serializzata con un nome di default che viene generato di default in base al tipo di espressione presa in causa.

```
	@abstractmethod
    def get_default_name(self) -> str:
        """Restituisce il nome predefinito se non è stato impostato un alias."""
        pass
```

Per cambiare il nome da quello di default a uno arbitrario esiste il metodo alias.

```
def alias(self, alias_name: str) -> "Expression":
        """Assegna un nuovo nome di output all'espressione."""
  
        self._alias_name = alias_name
        return self
```
#### 5.2 LiteralExpression
La classe LiteralExpression rappresenta costanti numeriche, booleane o stringhe che possono venir usate per comporre espressioni più complesse.
Generalmente si usano senza alias.

Hanno un valore e come i Field degli schemi hanno associato un DataTypes.
Se il DataTypes non viene passato al costruttore si prova a dedurne il tipo fra alcuni dei tipi elementari di Python.

```
def _infer_literal_type(val: Any) -> DataTypes:
    """Inferisce il DataType a partire da un valore nativo Python."""
  
    if isinstance(val, bool):
        return DataTypes.BOOLEAN
    elif isinstance(val, int):
        return DataTypes.INT
    elif isinstance(val, float):
        return DataTypes.DOUBLE
    elif isinstance(val, str):
        return DataTypes.STRING
    else:
        raise TypeError(f"Impossibile inferire il DataType per il valore {val} ({type(val)})")
        
class LiteralExpression(Expression):
    """Rappresenta una costante con relativo DataType."""
  
    def __init__(self, value: Any, data_type: Optional[DataTypes] = None):
        super().__init__()
        self.value = value
        self.data_type = data_type if data_type is not None 
					        else _infer_literal_type(value)        
```

Per evitare di scrivere ogni volta il costruttore esplicito ogni volta esiste la funzione helper "lit" che lo chiama.

```
def lit(value: Any, data_type: Optional[DataTypes] = None) -> LiteralExpression:
    """Crea una LiteralExpression per un valore costante."""
    
    return LiteralExpression(value, data_type)
```
#### 5.3 ColRefExpression
Come si può intuire dal nome ColRefExpression rappresenta una colonna della tabella a cui verrà applicata quest'espressione.

Si costruiscono a partire da una stringa che deve essere il nome della colonna da rappresentare, viene anche usata come nome dell'espressione.

```
class ColRefExpression(Expression):
    """Riferimento a una colonna esistente nello Schema."""
  
    def __init__(self, column_name: str):
        super().__init__()
        self.column_name = column_name
  
    def get_default_name(self) -> str:
        return self.column_name
```

Il tipo reso dall'espressione dipende dallo schema della tabella a cui la si applica.

```
def get_type(self, schema: Schema) -> DataTypes:
        return schema.get_type_for(self.column_name)
        #se non c'è la colonna lancia un'eccezione
```

L'espressione in sé non conserva il tipo, questo metodo viene chiamato soltanto durante la fase di serializzazione della execute o per determinare il tipo di un'espressione composta, in ogni caso l'espressione è riutilizzabile.

```
expr = col("number")
expr.get_type(int_schema)     #INT
expr.get_type(float_schema)   #FLOAT
```
#### 5.4 BinaryOpExpression
La classe che si ottiene utilizzando gli operatori dei metodi magici, mantiene nel proprio stato i due operandi sotto forma di espressioni e l'operatore utilizzato.

```
class BinaryOpExpression(Expression):
    """Rappresenta un'operazione binaria tra due espressioni."""
  
    def __init__(self, left: Expression, op: str, right: Expression):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def get_default_name(self) -> str:
        return f"({self.left.get_name()} {self.op} {self.right.get_name()})"
```

Di nuovo il tipo varia in base allo schema su cui viene applicata l'espressione tuttavia adesso ci sono dei veri e propri controlli di tipo in base all'operatore utilizzato.

```
def get_type(self, schema: Schema) -> DataTypes:
        t_left = self.left.get_type(schema)
        t_right = self.right.get_type(schema)
  
        #operatori di confronto
        if self.op in (">", "<", ">=", "<=", "==", "!="):
            if (t_left != t_right) and (not(t_left.is_number() and t_right.is_number())):
                raise TypeError(
                    f"Non si può fare {t_left} {self.op} {t_right}."
                    f"I tipi devono essere lo stesso o entrambi numerici."
                )
            return DataTypes.BOOLEAN

        #operatori logici
        if self.op in ("&&", "||"):
            if not(t_left.is_bool() and t_right.is_bool()):
                raise TypeError(
                    f"Non si può fare {t_left} {self.op} {t_right}."
                    f"I tipi devono essere entrambi booleani."
                )
            return DataTypes.BOOLEAN
  
        #operatori aritmetici
        if self.op in ("+", "-", "*", "/"):
            return DataTypes.most_general_number(t_left, t_right)
  
        #non dovrebbe mai arrivarci dato che gli if devono essere comprensivi
        return t_left
```

E' chiaro che gli operatori aritmetici si possono fare solo se entrambi gli operandi sono numeri, confronti vanno fatti fra valori di tipi comparabili e la logica si applica ai booleani.
In future versioni si potrebbe avere anche l'opzione di "+" su stringhe o simili.

Gli operatori aritmetici rendono il tipo più generale fra i due tipi di numero secondo la seguente priorità basata su come i casting vengono gestiti in C++.

```
#la priorità numericamente più alta vince
priority = {
            DataTypes.INT: 1,
            DataTypes.BIGINT: 2,
            DataTypes.FLOAT: 3,
            DataTypes.DOUBLE: 4
}
#nel caso di BIGINT e FLOAT si perde precisione nel BIGINT che da 64 va a 32 bit
```
#### 5.5 AggregateExpression
Dato che vanno nella select anche le espressioni d'aggregazione sono rappresentate da espressioni.

Sono tutte la stessa classe ma con una funzione associata diversa, per crearle si utilizzano delle funzioni helper che associano la funzione corrispondente.

```
class AggFuncType(Enum):
    """Tipologie di funzioni di aggregazione supportate dalla Table API."""
  
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    #future funzioni statistiche?
    
#esempio con sum    
def sum(expr: Union[str, Expression]) -> AggregateExpression:
    """Calcola la somma dei valori della colonna o espressione target."""
  
    if isinstance(expr, str):
        target = col(expr)
    else:
        target = expr    
    return AggregateExpression(AggFuncType.SUM, target)
```

Il costruttore appunto prende l'espressione target su cui va calcolata la funzione d'aggregazione e la funzione d'aggregazione stessa.

```
class AggregateExpression(Expression):
    """
    Rappresenta una funzione di aggregazione come SUM o COUNT.
    Viene calcolata all'interno di raggruppamenti (group_by) o globalmente.
    Nel secondo caso nella select possono esserci altri campi.
    """

    def __init__(
        self,
        func_type: AggFuncType,
        target_expr: Optional[Expression] = None
    ) -> None:
        super().__init__()
        self.func_type = func_type
        self.target_expr = target_expr
        self.is_distinct = False
```

Ogni AggregateExpression ha un flag "distinct" che indica se la funzione d'aggregazione deve considerare solo i valori unici dell'espressione target.
Si può porre a True questo flag con il metodo distinct.

```
expr = avg("temperature")
#equivale a AVG("temperature")

expr = avg("temperature").distinct()
#equivale a AVG(DISTINCT("temperature"))
```

Un caso particolare è quello della COUNT che può essere utilizzata senza parametri (conta il numero di tuple) o con delle chiavi.
La funzione helper count chiama implicitamente distinct se ci sono delle chiavi di conteggio dato che senza non avrebbe senso l'operazione.

```
def count(expr: Optional[Union[str, Expression]] = None) -> AggregateExpression:
    """
    Calcola il numero di record (COUNT(*)) se expr è None, 
    altrimenti COUNT(DISTINCT expr).
    """
  
    if isinstance(expr, Expression):
        return AggregateExpression(AggFuncType.COUNT, expr).distinct()

    if isinstance(expr, str):
        return AggregateExpression(AggFuncType.COUNT, col(expr)).distinct()
  
    return AggregateExpression(AggFuncType.COUNT, None)
```

Il metodo get_type deve di nuovo effettuare dei controlli di tipo in base allo schema dato.
Come che con BinaryOpExpression si applicano regole di base come che la AVG rende un DOUBLE e va applicata su un tipo numerico. 

```
def get_type(self, schema: Schema) -> DataTypes:
        #COUNT rende un BIGINT perchè il numero di tuple è potenzialmente infinito
        if self.func_type == AggFuncType.COUNT:
            return DataTypes.BIGINT
  
        if self.target_expr is None:
            raise ValueError(f"L'aggregazione {self.func_type.value} richiede un'espressione target.")

        #calcola il tipo reso applicando lo schema all'espressione target
        input_type = self.target_expr.get_type(schema)

        #AVG rende sempre un DOUBLE
        if self.func_type == AggFuncType.AVG:
            if not input_type.is_number():
                raise TypeError(
                    f"L'aggregazione {self.func_type.value} richiede un tipo numerico, "
                    f"ricevuto: {input_type.name}"
                )
            return DataTypes.DOUBLE
  
        #SUM, MIN, MAX conservano il tipo numerico di input
        if self.func_type in (AggFuncType.SUM, AggFuncType.MIN, AggFuncType.MAX):
            if not input_type.is_number():
                raise TypeError(
                    f"L'aggregazione {self.func_type.value} richiede un tipo numerico, "
                    f"ricevuto: {input_type.name}"
                )
            return input_type
  
        #altrimenti si suppone di mantenere il tipo in input
        return input_type
```
#### 5.6 UnaryOpExpression
Versione unaria di BinaryOpExpression, ha comportamenti e metodi analoghi ma l'operatore si applica ad una solo espressione invece di due.

Al momento di scrittura è presente solo l'operatore di not logico con il relativo metodo magico in Expression e una funzione helper per comodità.

```
def __invert__(self) -> UnaryOpExpression:
        """
        Bitwise Not (~) usato per il not logico perché il not logico 
        non ha un metodo magico.
        """
        return UnaryOpExpression(self, "not")
```

Da notare il fatto che l'operatore effettivo che viene sovraccaricato è il not bit-a-bit che si usa con "~", il not logico non può essere sovraccaricato in Python così come l'and e l'or.

```
def neg(expr: Expression) -> UnaryOpExpression:
    """
    Helper per il not logico per evitare di usare ~.
    Rende la UnaryOpExpression con il not logico applicato 
    all'espressione di input.
    """
    return ~expr
```

Il funzionamento di UnaryOpExpression è poi similare a BinaryOpExpression con get_type che controlla che l'espressione di input sia di un tipo compatibile all'operatore utilizzato.
## 6.0 Schemi e Validità del GroupBy 
Quanto segue si applica sia ad aggregazioni globali (senza chiavi) che keyed, l'unica differenza fra le due è che l'operatore di group_by viene inserito in automatico dal metodo select di Table per le globali.

Il group_by è il primo (e per ora unico) operatore che necessità dell'operatore successivo per completarsi dato che è la select ad avere le aggregazioni.
Per questo non ci possono essere operatori fra il group_by e la relativa select.

La sintassi utilizzata è la seguente.
```
q = tab.group_by("key", window= w).select("key", avg("number")) 
```
#### 6.1 Ricavare le Aggregazioni e lo Schema
Le aggregazioni necessarie sono ricavate dal metodo aggregation_dependencies della classe Expression sulle espressioni di selezione.
- LiteralExpression e ColRefExpression rendono una lista vuota. 
- BinaryOpExpression rende l'unione delle liste delle sotto-espressioni. 
- UnaryOpExpression uguale ma con l'espressione singola.
- AggregateExpression rendono loro stesse tuttavia è da evidenziare il fatto che la AVG richiede anche l'aggiunta della SUM e della COUNT per essere calcolata.

Le AggregateExpression che vengono ricavate sulla base del loro nome di default utilizzato come firma indipendente dall'alias che viene gestito dopo nella select.

```
q = tab.group_by("key").select("key", avg("number"), avg("number").alias("media"))
```

Nell'esempio soprastante nello schema del GroupByOp sarà presente solo una volta la AVG dato che non avrebbe senso calcolare la stessa funzione due volte.
Questo però richiede di cambiare le espressioni di selezione in modo che entrambe abbiano come rifermento alla stessa colonna dello schema del group_by.

```
{
        "op_type": "SELECT",
        "expressions": [
            {
                "expr_type": "COL_REF",
                "name": "key",
                "data_type": "STRING"
            },
            {
                "expr_type": "COL_REF",
                "name": "AVG(number)",
                "data_type": "DOUBLE"
            },
            {
                "expr_type": "COL_REF",
                "name": "AVG(number)",
                "data_type": "DOUBLE",
                "alias": "media"
            }
        ],
        "schema_in": {    #lo schema di output del GroupBy
            "key": "STRING",
            "AVG(number)": "DOUBLE",
            "COUNT(*)": "BIGINT",
            "SUM(number)": "DOUBLE"
        },
        "schema_out": {
            "key": "STRING",
            "AVG(number)": "DOUBLE",
            "media": "DOUBLE"
        },
        .....
```

Questo cambio è responsabilità del metodo astratto rewrite_grouped della classe Expression che per ogni sottoclasse l'adatta nel modo corretto.
- LiteralExpression e ColRefExpression non cambiano.
- BinaryOpExpression riscrive le due sotto-espressioni.
- UnaryOpExpression uguale ma con l'espressione singola.
- AggregateExpression diventa il riferimento alla colonna basata sul nome di default. 
#### 6.2 Validità
In più il GroupBy richiede dei controlli semantici sulle selezioni fatte nella select.
In modo simile all'SQL non si permette la selezione di attributi non chiave.

```
q = tab.group_by("key").select("number")   #non valido

q = tab.group_by("key").select("key",avg("number") + 10)   #valido
```

Questi controlli di selezione vengono effettuati tramite il metodo "validate_grouped" delle espressioni:
- ColRefExpression: valida se la colonna è una chiave di raggruppamento.
- LiteralExpression: sempre valida.
- BinaryOpExpression: valida se sono valide le due sotto-espressioni.
- UnaryOpExpression: come BinaryOpExpression ma con l'espressione singola.
- AggregateExpression: sempre valida.
## 7.0 Durations e Windows 
Il modulo durations permette di esprimere delle durate temporali in modo simile a LiteralExpression con le costanti tipizzate.
L'uso principale delle durate è nelle finestre temporali e negli intervalli presenti nel modulo windows motivo per cui in questa sezione li vedremo entrambi.
#### 7.1 Classe Duration 
Un oggetto Duration rappresenta una durata con un certo valore e una certa unità di misura.
Le unità di misura disponibili sono appartenenti ad un'enumerazione come i DataTypes.
Due Duration sono uguali se hanno stessa unità e stesso valore.

```
class TimeTypes(Enum):
    """
    Rappresenta le unità di tempo supportate dalla Table API.
    """

    SECONDS = "SECONDS"
    MILLISECONDS = "MILLISECONDS"
    MINUTES = "MINUTES"
    MICROSECONDS = "MICROSECONDS"
    HOURS = "HOURS"
    DAYS = "DAYS"
  
class Duration:
    """
    Rappresenta una durata temporale utilizzata per finestre ed intervalli.
    """

    def __init__(self, value: int, unit: TimeTypes) -> None:
        if not isinstance(value, int):
            raise TypeError(
	            f"Il valore della durata deve essere un intero, 
		            ricevuto: {type(value)}"
            )
        self.value = value
        self.unit = unit
```

Per evitare d'inserire a mano le unità di misura sono presenti vari metodi statici di factory che istanziano un oggetto con unità fissa.

```
#sintassi equivalenti
dur = Duration(10, TimeTypes.MINUTES)

dur = Duration.minutes(10)
```

Per quanto si può inserire direttamente un intero di segno negativo come valore è anche disponibile un metodo magico per invertire il segno con "-".
Può darsi che in futuro si supporti somme e sottrazioni fra Durations.

```
dur = Duration.seconds(-10)

dur = - Duration.seconds(10)
```

Le durate negative possono essere usate soltanto all'interno degli intervalli temporali.

#### 7.2 Classe Window
Le finestre servono per delimitare porzioni di stream per il group_by e la join.
Questo può essere fatto considerando i valori il cui timestamp ricade in un determinato slot temporale (Time-Based o TB) o creando gruppi di un numero specifico di tuple (Count-Based o CB).

Le finestre poi sono dotate di un parametro "slide" che indica dopo quanto far cominciare la finestra successiva.
Se "slide" non è specificato è inizializzato pari a "size", in tal caso la finestra si dice Tumble, altrimenti Sliding.

La classe Window offre dei metodi statici per creare finestre TB o CB.
```
    @staticmethod
    def createTBWindow(size: Duration, slide: Optional[Duration] = None) -> Window:
        """
        Crea una finestra temporale con le specifiche date.
        Se la dimensione di slide non è specificata viene creata una 
        finestra Tumble.
        """
  
        return Window(WindowType.TIME, size, slide)

    @staticmethod
    def createCBWindow(size: int, slide: Optional[int] = None) -> Window:
        """
        Crea una finestra count-based con le specifiche date.
        Se la dimensione di slide non è specificata viene creata una 
        finestra Tumble.
        """
        
        return Window(WindowType.COUNT, size, slide)
```

Nel caso non venissero usati i metodi factory ma si volesse usare il costruttore esplicito è importante specificare che sia "slide" che "size" devono essere di tipo in accordo col tipo di finestra creata e non negativi.

```
class WindowType(Enum):
    """Tipologia di finestra supportata."""

    TIME = "TIME"    
    COUNT = "COUNT"  
    #futura OVER window?
  
class Window:
    """
    Rappresenta la configurazione di una finestra Tumble o Sliding
    di tipo temporale o count-based.
    Sia il parametro size che slide devono essere > 0.
    """
  
    def __init__(
        self,
        window_type: WindowType,
        size: Union[int, Duration],
        slide: Optional[Union[int, Duration]] = None
    ) -> None:
	    #body
```
#### 7.3 Interval
L'oggetto Interval rappresenta un intervallo di tempo centrato nel timestamp attuale utilizzato nelle IntervalJoin.

Nel pratico gestisce due Duration: lower_bound e upper_bound.
Sia lower_bound che upper_bound possono essere negativi, obbligatorio che il primo sia strettamente minore del secondo e che abbiano la stessa unità temporale.
(questo perché per ora non ci sono confronti fra unità temporali diverse).

```
class Interval:
    """
    Rappresenta un intervallo temporale [lower_bound, upper_bound]
    utilizzato per configurare le Interval Join tra due stream.
    """

    def __init__(
        self,
        lower_bound: Duration,
        upper_bound: Duration
    ) -> None:
	    #body
```
#### 7.4 TimeCol
TimeCol è l'ultima classe presente in durations, serve all'ambiente per capire da quale colonna del file sorgente ricavare il timestamp.
A tempo di scrittura non è chiaro come dovranno essere formattati i file o come verranno istanziati gli operatori sorgente a livello WindFlow quindi c'è poco da dire.

```
class TimeCol:
    """
    Rappresenta una colonna da cui estrarre il timestamp nella sorgente.
    """

    def __init__(self, name: str, unit: TimeTypes):
        self.name = name
        self.unit = unit
        
    #body
```

```
#esempio d'uso
tc = TimeCol("timestamp", TimeTypes.MILLISECONDS)
tab = env.table_from_file("filepath", schema, "nome", tc)
```

E' importante dire che TimeCol è di necessaria presenza in ogni tabella nel caso la politica dell'ambiente sia segnata ad EVENT_TIME, in caso contrario va omessa. 
(maggiori dettagli nella sezione 8).
## 8.0 TableEnvironment
L'ambiente tiene traccia di tutte le tabelle create e permette di creare sia Table sorgenti che Query ma la sua funzione principale è quella di serializzare le query in JSON a seguito di un execute.
#### 8.1 Parallelismo e Politiche Temporali 
Per l'uso più essenziale dell'API l'ambiente può essere creato senza alcun parametro d'input.
```
env = TableEnvironment()
tab = env.table_from_file(...)
.....
```
##### 8.1.1 Grado di Parallelismo
Si può inizializzare l'ambiente con un valore di parallelismo "par" che indica il numero di thread che verranno istanziati a livello di WindFlow per gli operatori parallelizzabili.

```
env = TableEnvironment(par=2)
#di default par= 1
```

In WindFlow è possibile definire un diverso parallelismo per ogni singolo operatore, per la versione attuale dell'API ci si limita ad avere un parametro comune all'intero ambiente.
E' probabile che in una versione futura si possa decidere il grado di parallelismo alla granularità della singola Query.
##### 8.1.2 Politiche Temporali
A seconda di come si sceglie di gestire il timestamp delle tuple variano performance e i costrutti che si possono utilizzare.

Ci sono tre politiche temporali supportate:
- NO_POLICY: politica di default, non si possono usare finestre temporali ed intervalli, non supporta TimeCol nelle tabelle sorgente.
- INGRESS_TIME: pone il timestamp pari all'attimo in cui la tupla viene processata, non supporta TimeCol nelle tabelle sorgente.
- EVENT_TIME: il timestamp è ricavato tramite la TimeCol obbligatoria della tabella sorgente.

```
#esempi d'inizializzazione con i vari parametri
env1 = TableEnvironment()                                  #par = 1, NO_POLICY
env2 = TableEnvironment(policy= TimePolicy.INGRESS_TIME)   #par = 1
env3 = TableEnvironment(par= 2, policy= TimePolicy.EVENT_TIME)
```

Durante la serializzazione e la creazione di nuove tabelle sorgenti ci sono controlli per verificare la compatibilità con la politica temporale utilizzata.
#### 8.2 Creare tabelle sorgenti e Query
Come visto più volte durante questa documentazione le tabelle sorgenti dei flussi di dati vanno inserite manualmente nell'ambiente.

```
def table_from_file(
            self,
            file_path: str,
            schema: Schema,
            name: Optional[str] = None,
            time_col: Optional[TimeCol] = None
        ) -> Table:
        """
        Crea uno Data Stream sorgente a partire da un file.
        Istanzia una Table associata allo schema, le assegna un ID univoco 
        e la registra.
        Deve avere "time_col" solo e soltanto se la politica temporale 
        è EVENT_TIME.
        """
```

```
#esempi d'utilizzo
tab1 = env.table_from_file(filepath, schema)
tab2 = env.table_from_file(filepath, schema, time_col= tcol)
tab3 = env.table_from_file(filepath, schema, "nome", tcol)
```

Alla creazione di una tabella sorgente le informazioni inerenti al filepath e alla TimeCol vengono mantenute nell'ambiente in una mappa sources_config e verranno usati durante la serializzazione della tabella.

WindFlow ha anche l'opzione di ricevere dati via Kafka e RocksDB, per ora la Table API si limita ad utilizzare file di testo.

Se non viene specificato un nome il table_id della tabella viene generato automaticamente in base al numero di tabelle (includendo le Query) già presenti nell'ambiente.
Analogamente Il nome delle Query viene generato a partire da quello della tabella madre se il Draft non è stato rinominato.
Due tabelle con lo stesso nome non possono essere inserite nello stesso ambiente.

```
tab1 = env.table_from_file(filepath, schema, "pippo")
#table_id = "pippo"

q = tab.select(...)
#table_id: "pippo_query_2"        #2 perchè è la seconda tabella nell'env

tab3 = env.table_from_file(filepath, schema)
#table_id: "source_stream_file_3"

tab4 = env.table_from_file(filepath, schema, "pippo_query_2")
#ValueError
```

Le Query vengono create implicitamente dai metodi di selezione chiamando l'apposito metodo dell'ambiente a cui appartiene la tabella madre.

```
def create_query(self, 
	schema: Schema, 
	parent_table: str, 
	root_op: Operator,
    name: Optional[str] = None
    ) -> Query:
        """
        Crea e registra nell'ambiente una nuova Table derivata a 
        seguito dell'applicazione di una query.
        Se il Draft aveva un nome quello sarà il table_id della Query creata.
        """
```
#### 8.3 Execute
Il metodo execute è quello che deve essere chiamato per avviare la serializzazione in JSON della query e la sua successiva esecuzione da parte degli altri sotto-package dell'API.

```
env = TableEnvironment()
schema = (...)
filepath = "./input.csv"

tab = table_from_file(filepath, schema, "input_source")
tab.name_draft("bella_query")

q = (...)

env.execute(q)
#crea il file "bella_query.json"
```
##### 8.3.1 Query da Serializzare
Nel caso ci siano più Query da serializzare ognuna di esse avrà il proprio file JSON così da evitare di avere una stessa Query più volte all'interno di uno stesso file.
Vengono creati i file per tutte e sole le Query che sono necessarie allo svolgimento della Query target del metodo execute.
Questo processo viene svolto dal metodo  collect_referenced_queries. 

```
tab = env.table_from_file(..., "input_source")

tab.name_draft("query1")
q1 = (...)

tab.name_draft("query2")
q2 = (...)

tab.name_draft("query3")
q3 = (...)

q1.name_draft("query_finale")
qf = q1.union(q3).select(...)

env.execute(qf)
#crea:
# "query1.json", "query3.json" e "query_finale.json"
#query2 non è necessaria e quindi non viene serializzata
```

Le tabelle sorgente non vengono serializzate in JSON ma sono presenti all'interno dei singoli file sotto forma di operatori di From che descrivono come ricavare l'input.
I FromOp vengono creati autonomamente dall'ambiente quando giunge ad un TableRefOp relativo ad una tabella sorgente.
Ogni FromOp verrà convertito in un operatore Source con parallelismo par ad uno per garantire che ci siano in circolo il giusto numeri di tuple.
##### 8.3.2 Parametri di Execute 
Per quanto si può utilizzare execute senza parametri, al di fuori della Query target, come visto finora ce ne sono alcuni che richiedono una spiegazione.

```
def execute(self, 
	query: Query, 
	output_dir: str = ".", 
	rexecute: bool = False
	) -> Any:
```

Il parametro output_dir specifica in che directory andranno inseriti i file JSON generati dalla serializzazione.
Di default è la directory corrente ma si può specificare un qualsiasi filepath.

Il parametro rexecute se posto a True fa riserializzare una Query il cui file JSON è già presente nella output_dir.
Di default è False per evitare di riscrivere più volte un file identico scritto poco prima, tuttavia può essere utile in fase di testing in cui si cambia la logica delle query per non dover eliminare i file JSON ogni volta.

Attenzione però che se l'esecuzione di una query precedente sta leggendo il file durante la sovrascrittura tale esecuzione non andrà a compimento.
#### 8.4 Esecuzione del Livello Inferiore
Attualmente non implementata dato che il livello inferiore (parser e codegen) non esiste. 
#####TODO  