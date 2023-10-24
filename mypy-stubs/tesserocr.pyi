import enum

class PSM(enum.Enum):
    SINGLE_LINE = ...

class PyTessBaseAPI:
    def __init__(self, data_path: str, lang: str, psm: PSM = ...) -> None: ...
    def SetImageBytes(
            self,
            img: bytes,
            width: int,
            height: int,
            bytes_per_pixel: int,
            bytes_per_line: int,
    ) -> None: ...
    def GetUTF8Text(self) -> str: ...
