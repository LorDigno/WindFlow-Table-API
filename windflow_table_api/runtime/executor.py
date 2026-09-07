# windflow_table_api/runtime/executor.py
from pathlib import Path
import subprocess
from windflow_table_api.api.job_handle import JobHandle

from .cmake_manager import CMakeManager
from .compiler import CppCompiler


class Executor:
  """Entry point del runtime: gestisce CMake, compilazione e lancio del processo nativo."""

  def __init__(self, work_dir: Path) -> None:
      self.work_dir = Path(work_dir)
      self.build_dir = self.work_dir / "build"
      self.logs_dir = self.work_dir / "logs"

      self.cmake_mgr = CMakeManager(work_dir=self.work_dir)
      self.compiler = CppCompiler(
        source_dir=self.work_dir, build_dir=self.build_dir
      )

  def run_query(self, query_id: str) -> JobHandle:
      #setup del cmake
      self.cmake_mgr.ensure_target(query_id)

      #compilazione sincrona
      binary_path = self.compiler.compile(query_id)

      #lancio del processo separato con l'esecuzione
      self.logs_dir.mkdir(parents=True, exist_ok=True)
      out_file = self.logs_dir / f"{query_id}.stdout.log"
      err_file = self.logs_dir / f"{query_id}.stderr.log"

      out_fp = open(out_file, "w", encoding="utf-8")
      err_fp = open(err_file, "w", encoding="utf-8")

      proc = subprocess.Popen(
          [str(binary_path)],
          stdout=out_fp,
          stderr=err_fp,
          cwd=self.build_dir,
          start_new_session=True,
      )

      #rendo il JobHandle per il monitoraggio
      return JobHandle(
          query_id=query_id,
          process=proc,
          stdout_log=out_file,
          stderr_log=err_file,
      )