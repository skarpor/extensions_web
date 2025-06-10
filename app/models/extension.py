from pydantic import BaseModel
from typing import Optional, List


class ExtensionConfig(BaseModel):
    id: str
    name: str
    description: str
    endpoint: str
    enabled: bool = False
    config: dict = {}
    has_config_form: Optional[bool] = None
    documentation: Optional[dict] = None
    showinindex: bool = True
    return_type: str = "html"
    has_query_form: Optional[bool] = None
class UploadExtension(BaseModel):
    name: str
    description: str

class UpdateExtension(BaseModel):
    name: str
    description: str
    endpoint: str
    enabled: bool
    config: dict
    showinindex: bool
    return_type: str
