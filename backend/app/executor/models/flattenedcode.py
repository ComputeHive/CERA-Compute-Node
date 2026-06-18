from typing import Dict, Optional

from pydantic import BaseModel


class FlattenedCode(BaseModel):

    requirements: str
    code_deps: str
    function_content: str
    function_name: str
    input_schema: Optional[Dict[str, Optional[str]]] = None
