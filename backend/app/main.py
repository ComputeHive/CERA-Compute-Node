from contextlib import asynccontextmanager
from pathlib import Path
import sys
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from app.services.executor import executor
from app.api.routes import tools
from app.lib.utils import load_state_file, edit_state_file
from app.config import settings
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_state = load_state_file()
    await executor.run(["sudo", "bash","setup_cera_user.sh"],cwd="./scripts")
    yield
    # TODO: Add Shut down Behaviour
    edit_state_file(app.state.app_state)
app = FastAPI(title=settings.APP_NAME,lifespan=lifespan)
app.include_router(tools.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("app.main:app",host="localhost",port=8000,reload=True)
