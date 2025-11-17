from contextlib import asynccontextmanager
from fastapi.applications import FastAPI


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    try:
        yield
    except Exception as e:
        raise e
    finally:
        ...
