
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class chatRequest(BaseModel):
    """incoming chat request"""
    message: str = Field(..., min_length=1, max_length=10000, description="The user's message to the chatbot.")
    thread_id: str = Field(default="default", description="Unique identifier for the conversation thread.")

class chatResponse(BaseModel):
    """outgoing chat response"""
    response: str 
    thread_id: str 
    model_used: str
    cached: bool = False
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The time when the response was generated.")


class HealthCheckResponse(BaseModel):
    """response for health check endpoint"""
    status: str = "ok"
    environment: str
    version: str = "1.0.0"
    checks: dict ={}

class MetricsResponse(BaseModel):
    """response for metrics endpoint"""
    total_requests: int
    total_errors: int
    error_rate: float
    avg_latency_ms: float
    cache_hit_rate: int
    total_input_tokens: int
    total_output_tokens: int

class ErrorResponse(BaseModel):
    """standard error response model"""
    error: str
    details: str |None = None
    request_id: str| None = None