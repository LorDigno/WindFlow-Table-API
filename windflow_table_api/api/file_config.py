from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from .durations import Duration
from .schema import Schema
from pathlib import Path

class SplitSize:
    """
    Classe rappresentante la SplitSize per sorgenti parallele.
    Con i costruttori statici appositi converte in bytes  la grandezza di altre unità di misura.
    """

    bytes: int

    def __init__(self, size: int):
        self.bytes = size

    @staticmethod
    def kilobytes(size: int):
        return SplitSize(size * 1024)

    @staticmethod
    def megabytes(size: int):
        return SplitSize(size * 1024 * 1024)

    @staticmethod
    def gigabytes(size: int):
        return SplitSize(size * 1024 * 1024 * 1024  )

class FileFormat(Enum):
    """
    Formati supportati di input.
    """
    CSV = "csv"

class InputFileConfiguration:
    filepath: Path
    file_format: FileFormat
    schema: Schema
    has_header: bool
    is_ordered: bool
    delay: Optional[Duration]
    time_col: Optional[str]
    split_size: int

    def __init__( self,
        path: Path,
        format: FileFormat,
        schema: Schema,
        has_header: bool,
        order: bool,
        split_size: SplitSize = SplitSize(0),
        time_col: Optional[str] = None,
        delay: Optional[Duration] = None
    ):
        resolved_path = path.resolve().absolute()
        if not resolved_path.is_file():
            raise FileNotFoundError(
                f"[TABLE API] Il file di input non esiste: {resolved_path}"
            )
        
        if not order and delay is None:
            raise ValueError(
                "Per sorgenti non ordinate (order=False) è obbligatorio specificare un 'delay' di watermark."
            )
        if order and delay is not None:
            raise ValueError(
                "Per sorgenti ordinate (order=True) non è consentito specificare un 'delay'."
            )

        if time_col is not None and not schema.has_field(time_col):
            raise ValueError(
                "La TimeCol deve essere una colonna presente nello schema."
                f"\nFornita: {time_col} per {schema}."
            )

        
        self.filepath = resolved_path
        self.file_format = format
        self.schema = schema
        self.has_header = has_header
        self.time_col = time_col
        self.is_ordered = order
        self.delay = delay
        self.split_size = split_size.bytes

    def to_dict(self) -> Dict[str, Any]:
        dict = {
            "filepath": str(self.filepath),
            "file_format": self.file_format.name,
            "header": self.has_header,
            "time_col": self.time_col,
            "order": self.is_ordered,
            "delay": self.delay.to_dict() if self.delay else None,
            "split_size": self.split_size
        }
        return dict
    