from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class AddRowsReq(BaseModel):
    model_config = ConfigDict(extra='ignore')
    rows: list[list[Any]]
    filename: str
    headers: Optional[list[str]]
