from pathlib import Path
import subprocess


class CompilationError(Exception):
  """Sollevata quando la compilazione C++ fallisce."""

  pass


class CppCompiler:

    def __init__(self, source_dir: Path, build_dir: Path):
        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)

    def compile(self, query_id: str) -> Path:
        """Configura e compila solo l'eseguibile della query richiesta."""

        conf_cmd = [
            "cmake",
            "-S",
            str(self.source_dir),
            "-B",
            str(self.build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
        ]

        res_conf = subprocess.run(conf_cmd, capture_output=True, text=True)
        if res_conf.returncode != 0:
            raise CompilationError(
                f"CMake configure failed:\n{res_conf.stderr or res_conf.stdout}"
            )

        build_cmd = [
            "cmake",
            "--build",
            str(self.build_dir),
            "--target",
            query_id,
            "--",
            "-j",
        ]

        res_build = subprocess.run(build_cmd, capture_output=True, text=True)
        if res_build.returncode != 0:
            raise CompilationError(
                f"Compilazione C++ fallita per '{query_id}':\n{res_build.stderr or res_build.stdout}"
            )

        bin_path = self.build_dir / query_id
        if not bin_path.exists():
            raise FileNotFoundError(f"Binario generato non trovato in: {bin_path}")

        return bin_path
    