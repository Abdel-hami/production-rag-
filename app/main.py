import time
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.security import validate_input, validate_output
from app.models import chatRequest, chatResponse, ErrorResponse, HealthCheckResponse, MetricsResponse
from app.cache import RedisSemanticCache
from app.agent import ProductionAgent
from app.monitoring import MetricsCollector
from app.config import get_settings
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    global security, cache, metrics, agents
    settings = get_settings()

    logger.info(f"Starting production0api app in {settings.app_env} mode...")
    
    cache = RedisSemanticCache()
    metrics = MetricsResponse()
    agents = ProductionAgent()
    monitoring = MetricsCollector()
    logger.info("all components started...")
    yield
    logger.info(f"shutting down...",extra={"extra_data":monitoring.get_summary()})

## setup limiter
limiter = Limiter(key_func=get_remote_address) ## it tracks requests per ip address
## setup app
app = FastAPI(
    title="LangGraph Production API",
    description="A production-ready API for LangGraph.",
    version="1.0.0",
    lifespan=lifespan)

app.state.limiter = limiter

## exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded): 
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Rate limit exceeded. Please try again later."}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

