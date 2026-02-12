from fastapi import FastAPI
from backend.app.api.routes import tools

app = FastAPI(title="CERA Compute Node Backend")


app.include_router(tools.router, prefix="/api")
