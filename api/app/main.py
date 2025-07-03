import sentry_sdk
import logging
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session
import time
from sqlalchemy.exc import OperationalError



from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine, init_db


from fastapi import Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    max_retries = 10
    delay = 2
    for attempt in range(max_retries):
        try:
            with Session(engine) as session:
                logger.info("Trying to initialize DB (attempt %d)...", attempt + 1)
                init_db(session)
                logger.info("DB initialized successfully.")
                break
        except OperationalError as e:
            logger.warning("DB not ready yet (attempt %d): %s", attempt + 1, e)
            time.sleep(delay)
    else:
        logger.error("DB could not be reached after %d attempts.", max_retries)
        raise RuntimeError("Database connection failed during startup.")
    yield
    engine.dispose()
    logger.info("Database connections closed")

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        #allow_origins=settings.all_cors_origins,
        allow_origins=["*"],  # For development purposes, allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_V1_STR)



    
