from pathlib import Path

class CMakeManager:
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.cmake_path = self.work_dir / "CMakeLists.txt"

        #per ora con directory statiche per i test
        #risale da windflow_table_api/runtime/ fino alla root
        self.repo_root = Path(__file__).resolve().parents[2]

        #directory con le librerie
        inc_root = self.repo_root / "include"

        self.include_dirs = [
            inc_root,
            inc_root / "WindFlow" / "wf",
            inc_root / "fastflow",
            inc_root / "Table_WindFlow",
            self.work_dir,  
        ]

    def ensure_target(self, query_id: str) -> None:
        """Garantisce la presenza del target eseguibile nel CMakeLists.txt."""
        if not self.cmake_path.exists():
            self._create_base_cmake()

        content = self.cmake_path.read_text(encoding="utf-8")
        target_declaration = f"add_executable({query_id}"

        #se non c'è il target si aggiunge
        if target_declaration not in content:
            self._append_target(query_id)

    def _create_base_cmake(self) -> None:
        # Genera le inclusioni nel file CMakeLists.txt
        inc_str = "\n    ".join(f'"{d}"' for d in self.include_dirs)

        base_content = f"""cmake_minimum_required(VERSION 3.16)
            project(WindFlowGeneratedQueries CXX)

            set(CMAKE_CXX_STANDARD 17)
            set(CMAKE_CXX_STANDARD_REQUIRED ON)
            set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

            find_package(Threads REQUIRED)

            include_directories(
                {inc_str}
            )
            """
        self.cmake_path.write_text(base_content, encoding="utf-8")

    def _append_target(self, query_id: str) -> None:
        """Aggiunge la regola di compilazione e linking per la query specifica."""
        target_block = f"""
            # --- Target per Query: {query_id} ---
            add_executable({query_id} {query_id}_main.cpp)
            target_link_libraries({query_id} PRIVATE Threads::Threads pthread)
            """
        with open(self.cmake_path, "a", encoding="utf-8") as f:
            f.write(target_block)    