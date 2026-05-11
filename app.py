"""
DuckDuckGo AI to OpenAI-Compatible API Proxy
A FastAPI-based proxy server that wraps DuckDuckGo's free AI chat models
into an OpenAI-compatible API with custom API key authentication.
"""

import os
import json
import time
import asyncio
import hashlib
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

import httpx
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("DUCKDUCKGO_API_KEY", "sk-duckduckgo-default-key-change-me")
DUCKDUCKGO_API_BASE = "https://duckduckgo.com/duckchat/v1"
VQD_REFRESH_INTERVAL = 3600  # 1 hour

# Model mapping
MODEL_MAPPING = {
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-5-mini": "gpt-5-mini",
    "claude-3-5-haiku": "claude-3-5-haiku-latest",
    "llama-4-scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "mistral-small": "mistralai/Mistral-Small-24B-Instruct-2501",
    "gpt-4o": "gpt-4o-mini",  # Default fallback
    "gpt-4": "gpt-4o-mini",   # Default fallback
    "gpt-3.5-turbo": "gpt-4o-mini",  # Default fallback
}

# Static headers and values (from reverse engineering)
STATIC_VQD_HASH_1 = "eyJzZXJ2ZXJfaGFzaGVzIjpbImRQSlJJTWczZnFYQXIvaStaa3c2cEpFVzEwckdTdmxJVlVkNlFsOVRGWXc9IiwiMUN3Qzg3N0Q3WXE1dzlEeTc4UjhBVi9qZVZWaUlYbmV0Q0xvckx3c01QZz0iLCJQSzc3TGc2L25weDdWQ2J2UWxsTEhBR3cyenJIVmEvQUFBRFBhQTl1ekVRPSJdLCJjbGllbnRfaGFzaGVzIjpbImxWblI0MStCMVFWZ0o4d0hhMUdBNmdxR0JoSjlWdjN5K0dISkdGekJmTGM9IiwiVS9RRUc2RE1qdEU4V2hHU1FxOUU1Z0VGNmw1SWJrNk9NVlBuY01DU1licz0iLCJ6SURsYUNvZG9JUjNwbTNSVTlWOUJXaUJkZDJqenRMODAyN0VYTHhkWll3PSJdLCJzaWduYWxzIjp7fSwibWV0YSI6eyJ2IjoiNCIsImNoYWxsZW5nZV9pZCI6ImM4M2Q0ZTc5NTU2MjJmZjU3Mzc0ZDUzOTk2ZjliMmJhZGE2ZDQxZTMzNDM1ZjVlNzMyYjFmNmZjNmQ0ZTE1NzVoOGpidCIsInRpbWVzdGFtcCI6IjE3NTIxNTU3Nzc4NjYiLCJvcmlnaW4iOiJodHRwczovL2R1Y2tkdWNrZ28uY29tIiwic3RhY2siOiJFcnJvclxuYXQgRSAoaHR0cHM6Ly9kdWNrZHVja2dvLmNvbS9kaXN0L3dwbS5jaGF0LjcwZWFjYTZhZWEyOTQ4YjBiYjYwLmpzOjE6MTQ4MjUpXG5hdCBhc3luYyBodHRwczovL2R1Y2tkdWNrZ28uY29tL2Rpc3Qvd3BtLmNoYXQuNzBlYWNhNmFlYTI5NDhiMGJiNjAuanM6MToxNjk4NSIsImR1cmF0aW9uIjoiNTgifX0="
STATIC_FE_SIGNALS = "eyJzdGFydCI6MTc1MjE1NTc3NzQ4MCwiZXZlbnRzIjpbeyJuYW1lIjoic3RhcnROZXdDaGF0IiwiZGVsdGEiOjc1fSx7Im5hbWUiOiJyZWNlbnRDaGF0c0xpc3RJbXByZXNzaW9uIiwiZGVsdGEiOjEyNH1dLCJlbmQiOjQzNDN9"
STATIC_FE_VERSION = "serp_20250710_090702_ET-70eaca6aea2948b0bb60"

# Global state for VQD token
vqd_cache = {
    "token": None,
    "last_updated": 0
}


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: Optional[Message] = None
    delta: Optional[Dict[str, str]] = None
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Dict[str, int]] = None


def get_browser_headers() -> Dict[str, str]:
    """Get headers that mimic a real browser request."""
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Authority": "duckduckgo.com",
        "Cache-Control": "no-store",
        "DNT": "1",
        "Priority": "u=1, i",
        "Referer": "https://duckduckgo.com/",
        "Sec-CH-UA": '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-vqd-accept": "1",
    }


def get_cookies() -> Dict[str, str]:
    """Get essential cookies for DuckDuckGo."""
    return {
        "5": "1",
        "dcm": "3",
        "dcs": "1",
    }


async def refresh_vqd_token() -> str:
    """Fetch a fresh VQD token from DuckDuckGo status endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = get_browser_headers()
            cookies = get_cookies()
            
            response = await client.get(
                f"{DUCKDUCKGO_API_BASE}/status",
                headers=headers,
                cookies=cookies,
            )
            response.raise_for_status()
            
            vqd_token = response.headers.get("x-vqd-4")
            if not vqd_token:
                logger.warning("No VQD token in response headers")
                return None
            
            vqd_cache["token"] = vqd_token
            vqd_cache["last_updated"] = time.time()
            logger.info("VQD token refreshed successfully")
            return vqd_token
    except Exception as e:
        logger.error(f"Failed to refresh VQD token: {e}")
        return vqd_cache.get("token")


async def get_vqd_token() -> str:
    """Get VQD token, refreshing if necessary."""
    current_time = time.time()
    
    # Refresh if token is None or older than INTERVAL
    if vqd_cache["token"] is None or (current_time - vqd_cache["last_updated"]) > VQD_REFRESH_INTERVAL:
        return await refresh_vqd_token()
    
    return vqd_cache["token"]


def map_model(model: str) -> str:
    """Map OpenAI model names to DuckDuckGo model names."""
    return MODEL_MAPPING.get(model, "gpt-4o-mini")


def build_duckduckgo_payload(model: str, messages: List[Message]) -> Dict[str, Any]:
    """Build the payload for DuckDuckGo API."""
    return {
        "model": map_model(model),
        "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        "canUseTools": False,
        "canUseApproxLocation": False,
        "metadata": {
            "toolChoice": {
                "NewsSearch": False,
                "VideosSearch": False,
                "LocalSearch": False,
                "WeatherForecast": False,
            }
        },
    }


async def stream_chat_response(model: str, messages: List[Message]):
    """Stream chat response from DuckDuckGo API."""
    vqd_token = await get_vqd_token()
    if not vqd_token:
        raise HTTPException(status_code=503, detail="Failed to obtain VQD token")
    
    headers = get_browser_headers()
    headers["x-vqd-4"] = vqd_token
    headers["x-vqd-hash-1"] = STATIC_VQD_HASH_1
    headers["x-fe-signals"] = STATIC_FE_SIGNALS
    headers["x-fe-version"] = STATIC_FE_VERSION
    headers["Content-Type"] = "application/json"
    
    cookies = get_cookies()
    payload = build_duckduckgo_payload(model, messages)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DUCKDUCKGO_API_BASE}/chat",
                json=payload,
                headers=headers,
                cookies=cookies,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.atext()
                    logger.error(f"DuckDuckGo API error: {response.status_code} - {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"DuckDuckGo API error: {error_text[:200]}"
                    )
                
                # Check if we need to refresh VQD on 418 or 429
                if response.status_code in [418, 429]:
                    await refresh_vqd_token()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            yield 'data: [DONE]\n\n'
                            break
                        
                        try:
                            chunk = json.loads(data)
                            # Convert DuckDuckGo format to OpenAI format
                            message_content = chunk.get("message", "")
                            
                            openai_chunk = {
                                "id": f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
                                "object": "text_completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": message_content} if message_content else {},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse chunk: {data}")
                            continue
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to DuckDuckGo API timed out")
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def non_streaming_chat_response(model: str, messages: List[Message]) -> Dict[str, Any]:
    """Get non-streaming chat response from DuckDuckGo API."""
    vqd_token = await get_vqd_token()
    if not vqd_token:
        raise HTTPException(status_code=503, detail="Failed to obtain VQD token")
    
    headers = get_browser_headers()
    headers["x-vqd-4"] = vqd_token
    headers["x-vqd-hash-1"] = STATIC_VQD_HASH_1
    headers["x-fe-signals"] = STATIC_FE_SIGNALS
    headers["x-fe-version"] = STATIC_FE_VERSION
    headers["Content-Type"] = "application/json"
    
    cookies = get_cookies()
    payload = build_duckduckgo_payload(model, messages)
    
    full_response = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DUCKDUCKGO_API_BASE}/chat",
                json=payload,
                headers=headers,
                cookies=cookies,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.atext()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"DuckDuckGo API error: {error_text[:200]}"
                    )
                
                async for line in response.aiter_lines():
                    if not line.strip() or not line.startswith("data: "):
                        continue
                    
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        message_content = chunk.get("message", "")
                        if message_content:
                            full_response += message_content
                    except json.JSONDecodeError:
                        continue
        
        return {
            "id": f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": full_response},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg.content.split()) for msg in messages),
                "completion_tokens": len(full_response.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in messages) + len(full_response.split()),
            },
        }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to DuckDuckGo API timed out")
    except Exception as e:
        logger.error(f"Error in non-streaming response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Create FastAPI app
app = FastAPI(
    title="DuckDuckGo AI Proxy",
    description="OpenAI-compatible API proxy for DuckDuckGo AI",
    version="1.0.0",
)


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    """Verify API key for all requests."""
    # Skip verification for health check and models endpoint
    if request.url.path in ["/health", "/v1/models"]:
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/v1/models")
async def list_models():
    """List available models."""
    models = [
        {
            "id": model,
            "object": "model",
            "owned_by": "duckduckgo",
            "permission": [],
        }
        for model in MODEL_MAPPING.keys()
    ]
    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    
    if request.stream:
        return StreamingResponse(
            stream_chat_response(request.model, request.messages),
            media_type="text/event-stream",
        )
    else:
        response = await non_streaming_chat_response(request.model, request.messages)
        return response


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DuckDuckGo AI Proxy",
        "version": "1.0.0",
        "description": "OpenAI-compatible API proxy for DuckDuckGo AI",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat_completions": "/v1/chat/completions",
        },
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
