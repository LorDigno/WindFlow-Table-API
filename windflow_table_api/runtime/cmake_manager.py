from pathlib import Path
from typing import Optional


class CMakeManager:

    def __init__(
        self,
        work_dir: Path,
        windflow_include: Optional[Path] = None,
        fastflow_include: Optional[Path] = None,
        table_api_include: Optional[Path] = None,
    ):
        self.work_dir = Path(work_dir)
        self.cmake_path = self.work_dir / "CMakeLists.txt"
        self.windflow_inc = windflow_include or Path("/usr/local/include")
        self.fastflow_inc = fastflow_include or Path("/usr/local/include")
        self.table_api_inc = table_api_include or Path(".")

    def ensure_target(self, query_id: str) -> None:
        """Garantisce la presenza del target nel CMakeLists.txt."""
        if not self.cmake_path.exists():
            self._create_base_cmake()

        content = self.cmake_path.read_text(encoding="utf-8")
        target_declaration = f"add_executable({query_id}"

        # Se il target non esiste nel CMakeLists corrente, lo appendiamo
        if target_declaration not in content:
            self._append_target(query_id)

    def _create_base_cmake(self) -> None:
        base_content = f"""cmake_minimum_required(VERSION 3.16)
            set(CMAKE_CXX_STANDARD 17)
            set(CMAKE_CXX_STANDARD_REQUIRED ON)
            set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

            # Threading
            find_package(Threads REQUIRED)

            # Inclusioni di WindFlow, FastFlow e dei builder Table API
            include_directories(
                "{self.windflow_inc}"
                "{self.fastflow_inc}"
                "{self.table_api_inc}"
                "${{CMAKE_CURRENT_SOURCE_DIR}}"
            )
            """
        self.cmake_path.write_text(base_content, encoding="utf-8")

    def _append_target(self, query_id: str) -> None:
        target_block = f"""
            # --- Target per Query: {query_id} ---
            add_executable({query_id} {query_id}_main.cpp)
            target_link_libraries({query_id} PRIVATE Threads::Threads pthread)
            """
        with open(self.cmake_path, "a", encoding="utf-8") as f:
            f.write(target_block)
    