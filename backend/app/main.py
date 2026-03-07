from contextlib import asynccontextmanager
from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from app.api.routes import tools, vm
from fastapi.middleware.cors import CORSMiddleware
from app.services.vsock_listener import vsock_listener
from app.config import settings
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    vsock_listener.start()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(tools.router, prefix="/api")
app.include_router(vm.router, prefix="/api/vm")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
