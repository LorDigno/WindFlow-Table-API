from pathlib import Path
import subprocess
import time
from typing import Optional


class JobHandle:

    def __init__(
        self, query_id: str, process: subprocess.Popen, stdout_log: Path, stderr_log: Path
    ):
        self.query_id = query_id
        self.process = process
        self.stdout_log = stdout_log
        self.stderr_log = stderr_log
        self.pid = process.pid

    def is_running(self) -> bool:
        """Controlla se il binario WindFlow è ancora attivo."""
        return self.process.poll() is None

    def wait(self, timeout: Optional[float] = None) -> int:
        """Attende la terminazione naturale del programma (es.

        raggiungimento EOS).
        """
        return self.process.wait(timeout=timeout)

    def stop(self, timeout: float = 5.0) -> None:
        """Termina il processo in modo ordinato (SIGINT/SIGTERM poi SIGKILL)."""
        if not self.is_running():
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def get_out_logs(self, tail: int = 50) -> str:
        """Legge le ultime righe dei log."""
        if not self.stdout_log.exists():
            return ""
        with open(self.stdout_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-tail:])

    def get_err_logs(self, tail: int = 50) -> str:
        """Legge le ultime righe dei log."""
        if not self.stderr_log.exists():
            return ""
        with open(self.stdout_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-tail:])
    
