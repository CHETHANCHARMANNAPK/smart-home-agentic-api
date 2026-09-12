from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router
from app.api.hardware_routes import router as hardware_router
from app.mock_hardware.state import home_state


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Smart Home Agentic API",
    version="2.0.0",
    description=(
        "Safety-aware agentic smart-home API. Natural-language commands are planned into "
        "structured tool calls, validated by a deterministic policy layer, executed asynchronously, "
        "and verified against mock physical state."
    ),
    lifespan=lifespan,
)
app.include_router(router, prefix="/api/v1")
app.include_router(hardware_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "smart-home-agent", "version": app.version}


@app.get("/state", include_in_schema=False)
async def state():
    return home_state.snapshot()
