
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langsmith import traceable
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


from app.security import validate_input, validate_output
from app.models import chatRequest, chatResponse, ErrorResponse, HealthCheckResponse, MetricsResponse
from app.cache import RedisSemanticCache
from app.agent import ProductionAgent
from app.monitoring import MetricsCollector, RequesTimer
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
    metrics = MetricsCollector()
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
    logger.error(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Please try again later."}
    )


# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request: Request, exc: StarletteHTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.detail}
#     )



## endpoints

@app.post("/chat", response_model = chatResponse)
@limiter.limit(get_settings().rate_limit) ## apply rate limiting
@traceable(name="chat_endpoint")
async def chat(request: Request, body:chatRequest):
    """Flow:
        -> Security check (injection + PII masking)
        -> Cache lookup
        -> LangGraph agent invoke (if cache miss)
        -> Output validation
        -> Cache store
        -> Return response
    """

    with RequesTimer() as timer:
        security_notes = []

        ## step 1: security check

        result = await validate_input(body.message)
        # print(f"security check result: {result}")  
        security_notes.extend(result.warnings)
        cleaned_input = result.data
        # logger.info(f"cleaned input type: {type(cleaned_input)} cleaned_input: {cleaned_input}")
        # print(f"data: {result.data} warnings: {result.warnings} errors: {result.errors}")  
        if result.status == "failed":
            logger.warning(f"Security check failed for thread_id: {body.thread_id}. Warnings: {result['warnings']}")
            metrics.record_request(latency_ms=0,input_tokens=0,output_tokens=0,error=True)
            raise HTTPException(status_code=400, detail="your message blocked by our security checks")
        ## step 2: cache lookup

        cached_response = cache.get(cleaned_input)
        
        if cached_response:
            metrics.record_request(latency_ms=0,input_tokens=0,output_tokens=0,cache_hit=True)
            logger.info(f"Cache hit for thread_id: {body.thread_id}")
            return chatResponse(response=cached_response, thread_id=body.thread_id,model_used="cached", cached=True, processing_time_ms=0)
        
        ## step 3: langraph agent invoke
        try:
            logger.info(f"LangGraph agent invoke for thread_id: {body.thread_id}")
            result = agents.invoke(cleaned_input) ## invoking LangGraph agent: object dict can't be used in 'await' expression
            # print(f"LangGraph agent result: {result}")
        except Exception as e: 
            logger.error(f"Error invoking LangGraph agent: {e}")
            metrics.record_request(latency_ms=0,input_tokens=0,output_tokens=0, error=True)
            raise HTTPException(status_code=500, detail="Error processing your request. Please try again later.")

        response_text = result["response"]
        model_used = result["model_used"]

        ## step 4: output validation
        output_validation = await validate_output(response_text)
        # print(f"output validation: {output_validation}")
        # print(f"output validation: {output_validation.data}")
        security_notes.extend(output_validation.warnings)
        ## step 5: cache set
        cache.set(cleaned_input, output_validation.data)
    ## step 6: log and record metrics
    input_tokens = int(len(cleaned_input.split()) * 1.3) ## 1.3 is a rough estimate of token count from word count
    output_tokens = int(len(output_validation.data.split()) * 1.3)
    metrics.record_request(latency_ms=timer.elapsed_ms, input_tokens=input_tokens, output_tokens=output_tokens, cache_hit=False)
    if security_notes:
        logger.warning(f"Security warnings for thread_id: {body.thread_id}. Warnings: {security_notes}")
    return chatResponse(response=output_validation.data, thread_id=body.thread_id, model_used=model_used, cached=False, processing_time_ms=round(timer.elapsed_ms, 2))


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify the service is running."""
    settings = get_settings()
    checks = {
        "cache":cache is not None,
        "agent":agents is not None,
        "metrics":metrics is not None
    }
    all_healthy  = all(checks.values())
    return HealthCheckResponse(
        status= "healthy" if all_healthy else "error",
        environment=settings.app_env,
        version="1.0.0",
        checks=checks
    )

# metrics endpoint

@app.get("/metrics", response_model=MetricsResponse)
async def metrics_endpoint():
    summary = metrics.get_summary()
    return MetricsResponse(**summary)
