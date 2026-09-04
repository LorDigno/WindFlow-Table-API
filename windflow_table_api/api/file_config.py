from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from .durations import TimeCol, Duration
from .schema import Schema

class FileFormat(Enum):
    """
    Formati supportati di input.
    """
    CSV = "csv"

class InputFileConfiguration:
    filepath: str
    file_format: FileFormat
    schema: Schema
    has_header: bool
    is_ordered: bool
    delay: Optional[Duration]
    time_col: Optional[TimeCol]

    def __init__( self,
        path: str,
        format: FileFormat,
        schema: Schema,
        has_header: bool,
        time_col: Optional[TimeCol] = None,
        order: bool = True,
        delay: Optional[Duration] = None
    ):
        if not order and delay is None:
            raise ValueError(
                "Per sorgenti non ordinate (order=False) è obbligatorio specificare un 'delay' di watermark."
            )
        if order and delay is not None:
            raise ValueError(
                "Per sorgenti ordinate (order=True) non è consentito specificare un 'delay'."
            )
        
        self.filepath = path
        self.file_format = format
        self.schema = schema
        self.has_header = has_header
        self.time_col = time_col
        self.is_ordered = order
        self.delay = delay

    def to_dict(self) -> Dict[str, Any]:
        dict = {
            "filepath": self.filepath,
            "file_format": self.file_format.name,
            "header": self.has_header,
            "time_col": self.time_col.to_dict() if self.time_col else None,
            "order": self.is_ordered,
            "delay": self.delay.to_dict() if self.delay else None
        }
        return dict