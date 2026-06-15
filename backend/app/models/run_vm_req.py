from pydantic import BaseModel


class RunVMRequest(BaseModel):
    token: str
