from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from utility_maps import TYPE_MAP

@dataclass
class CppField:
    """Rappresenta un singolo campo all'interno dello struct C++."""

    name: str
    cpp_type: str
    json_type: str

@dataclass
class CppStruct:
    """
    Rappresenta uno struct C++ generato.
    Contiene sia i metadati dei campi che il codice C++ generato.
    """
    struct_name: str
    fields: List[CppField]
    needs_hash: bool = False
    
    @property
    def canonical_signature(self) -> Tuple[Tuple[str, str], ...]:
        """
        Firma canonica basata sulla sequenza ordinata di (nome_campo, tipo_cpp).
        Utilizzata come chiave per la deduplicazione degli struct identici.
        """
        return tuple(sorted((f.name, f.cpp_type) for f in self.fields))

class SchemaGenerator:
    """
    Gestisce la conversione degli schemi JSON in struct C++ e la loro deduplicazione.
    Tutti gli struct generati ordinano alfabeticamente i campi per valutare al meglio l'equivalenza fra schemi.
    """

    def __init__(self):
        #cache usata per non creare due volte schemi equivalenti fra loro
        self._struct_cache: Dict[Tuple[Tuple[str, str], ...], CppStruct] = {}

        #campi per la generatìzione dei nomi degli struct
        self._used_names: Set[str] = set()
        self._struct_counter: int = 0

        #setup di jinja
        templates_dir = Path(__file__).parent / "templates"
        self._jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def map_type(self, json_type: str) -> str:
        """
        Converte un tipo logico nel corrispondente tipo C++ nativo.
        Lancia KeyError se il tipo non è supportato.
        """

        if json_type not in TYPE_MAP:
            raise KeyError(f"Il tipo {json_type} non è supportato.")

        return TYPE_MAP[json_type]

    def get_or_create_struct(
        self, 
        schema_dict: Dict[str, str], 
        name_hint: str = "TupleStruct", 
        needs_hash: bool = False
    ) -> CppStruct:
        """
        Dato uno schema JSON:
        - Calcola la firma canonica (struct ordinato alfabeticamente).
        - Se esiste già uno struct equivalente nella cache, lo restituisce.
        - Altrimenti, genera un nuovo nome univoco, crea il CppStruct e lo salva in cache.
        """

        #costruzione dei field
        cpp_fields: List[CppField] = []
        for field_name, json_type in schema_dict.items():
            cpp_type = self.map_type(json_type)
            cpp_fields.append(
                CppField(name=field_name, cpp_type=cpp_type, json_type=json_type)
            )

        #struct temporaneo per verificare la presenza di uno equivalente
        temp_struct = CppStruct(struct_name="", fields=cpp_fields, needs_hash=needs_hash)
        signature = temp_struct.canonical_signature

        #controllo dell'equivalenza
        if signature in self._struct_cache:
            cached_struct = self._struct_cache[signature]

            #se ottiene la necessità dell'hash aggiunge il flag
            if needs_hash and not cached_struct.needs_hash:
                cached_struct.needs_hash = True

            return cached_struct

        #finalizzazione del nuovo struct
        unique_name = self._generate_unique_name(name_hint)
        real_struct = CppStruct(
            struct_name=unique_name, 
            fields=cpp_fields, 
            needs_hash=needs_hash
        )
        
        self._struct_cache[signature] = real_struct
        return real_struct

    def _generate_unique_name(self, hint: str) -> str:
        """
        Genera un nome univoco per lo struct basandosi sull'hint fornito.
        """

        #se è un nome nuovo lo registriamo e usiamo quello
        if hint not in self._used_names:
            self._used_names.add(hint)
            self._struct_counter += 1
            return hint

        #se esiste già si aggiunge un suffisso numerico
        self._struct_counter += 1
        new_name = f"{hint}_{self._struct_counter}"
        while new_name in self._used_names:
            self._struct_counter += 1
            new_name = f"{hint}_{self._struct_counter}"

        self._used_names.add(new_name)
        return new_name

    def render_all_structs(self, query_id:str) -> str:
        """
        Restituisce l'intero blocco di codice C++ contenente tutti gli struct 
        unici generati finora, pronto da essere inserito nel file .hpp o .cpp.
        """

        template = self._jinja_env.get_template("structs.hpp.jinja2")
        struct_list = list(self._struct_cache.values())

        #carico e renderizzo il template con gli struct richiesti
        return template.render(
            query_id=query_id,
            structs=struct_list
        )

    def write_header_file(self, output_dir: Path, query_id: str) -> Path:
        """
        Genera il file header C++ salvandolo come <output_dir>/<query_id>_structs.hpp.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        header_code = self.render_all_structs(query_id)
        file_path = output_dir / f"{query_id}_structs.hpp"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header_code)
            
        return file_path
