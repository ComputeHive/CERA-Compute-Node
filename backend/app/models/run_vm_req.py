from pydantic import BaseModel


class RunVMRequest(BaseModel):
    CPU: int
    RAM: int
    Disk: int
