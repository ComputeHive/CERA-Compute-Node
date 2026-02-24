from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from app.services.executor import executor
from app.api.routes import tools
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import uvicorn

app = FastAPI()

app = FastAPI(
    title=settings.APP_NAME,
)
app.include_router(tools.router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
