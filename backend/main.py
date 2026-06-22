import argparse
import asyncio

import aiohttp
import uvicorn
from app.api.routes import tools, vm
from app.config import app_config
from app.core.services.heartbeat import HeartbeatService
from app.core.task_service import TaskService
from app.observer import MessageObserver, message_observer
from app.utils.key_exchange import bootstrap_key_exchange
from app.utils.lib import Metrics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=app_config.APP_NAME)
app.include_router(tools.router, prefix="/api")
app.include_router(vm.router, prefix="/api/vm")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


METRICS_INTERVAL = 2


class MetricsSender:
    def __init__(self, observer: MessageObserver):
        self._observer = observer

    async def run(self) -> None:
        while True:
            data = await asyncio.to_thread(Metrics.collect_metrics)
            print(data)
            self._observer.update_metrics(data)
            await asyncio.sleep(METRICS_INTERVAL)


class Agent:

    async def start(self) -> None:
        print("Login during 15 seconds")
        await asyncio.sleep(15)
        async with aiohttp.ClientSession() as session:
            task_service = TaskService(session, message_observer)
            await bootstrap_key_exchange(session)
            tasks = [
                asyncio.create_task(MetricsSender(message_observer).run()),
                asyncio.create_task(
                    HeartbeatService(session, task_service).run()
                ),
                asyncio.create_task(task_service.run_poller()),
            ]
            try:
                await asyncio.gather(*tasks)
            finally:
                for t in tasks:
                    t.cancel()


async def main(port: int) -> None:
    config = uvicorn.Config(app, host="localhost", port=port)
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        Agent().start(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    asyncio.run(main(args.port))
