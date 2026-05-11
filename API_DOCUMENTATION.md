# API Documentation

Complete API reference for the DuckDuckGo AI Proxy server.

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints except `/health` and `/v1/models` require Bearer token authentication.

### Header Format

```
Authorization: Bearer sk-your-api-key-here
```

### Example

```bash
curl -H "Authorization: Bearer sk-duckduckgo-your-secure-key-here" \
  http://localhost:8000/v1/models
```

## Endpoints

### 1. Health Check

Check if the proxy server is running and healthy.

**Endpoint**: `GET /health`

**Authentication**: Not required

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Status Codes**:
- `200 OK`: Server is healthy

---

### 2. Root Information

Get general information about the proxy API.

**Endpoint**: `GET /`

**Authentication**: Not required

**Response**:
```json
{
  "name": "DuckDuckGo AI Proxy",
  "version": "1.0.0",
  "description": "OpenAI-compatible API proxy for DuckDuckGo AI",
  "endpoints": {
    "health": "/health",
    "models": "/v1/models",
    "chat_completions": "/v1/chat/completions"
  }
}
```

---

### 3. List Models

Get a list of all available AI models.

**Endpoint**: `GET /v1/models`

**Authentication**: Required

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "owned_by": "duckduckgo",
      "permission": []
    },
    {
      "id": "gpt-5-mini",
      "object": "model",
      "owned_by": "duckduckgo",
      "permission": []
    },
    {
      "id": "claude-3-5-haiku",
      "object": "model",
      "owned_by": "duckduckgo",
      "permission": []
    },
    {
      "id": "llama-4-scout",
      "object": "model",
      "owned_by": "duckduckgo",
      "permission": []
    },
    {
      "id": "mistral-small",
      "object": "model",
      "owned_by": "duckduckgo",
      "permission": []
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved models
- `401 Unauthorized`: Invalid or missing API key

---

### 4. Chat Completions

Create a chat completion with streaming or non-streaming response.

**Endpoint**: `POST /v1/chat/completions`

**Authentication**: Required

**Request Body**:
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": "Your message here"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 0.9
}
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model to use (see available models) |
| `messages` | array | Yes | Array of message objects with `role` and `content` |
| `stream` | boolean | No | Enable streaming responses (default: false) |
| `temperature` | float | No | Sampling temperature (0.0-2.0, default: 1.0) |
| `max_tokens` | integer | No | Maximum tokens in response |
| `top_p` | float | No | Nucleus sampling parameter (0.0-1.0) |

**Message Object**:
```json
{
  "role": "user|assistant|system",
  "content": "Message content"
}
```

#### Non-Streaming Response

**Status Codes**:
- `200 OK`: Successfully generated completion
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `503 Service Unavailable`: Failed to obtain VQD token
- `504 Gateway Timeout`: Request to DuckDuckGo API timed out

**Response**:
```json
{
  "id": "chatcmpl-abc123def456",
  "object": "text_completion",
  "created": 1705315845,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "This is the assistant's response."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  }
}
```

#### Streaming Response

When `stream: true`, the response is sent as Server-Sent Events (SSE).

**Response Format**: Each chunk is a JSON object prefixed with `data: `

```
data: {"id":"chatcmpl-abc123","object":"text_completion.chunk","created":1705315845,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"text_completion.chunk","created":1705315845,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: [DONE]
```

**Streaming Chunk Object**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "text_completion.chunk",
  "created": 1705315845,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "delta": {
        "content": "text chunk"
      },
      "finish_reason": null
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request

Returned when the request is invalid.

```json
{
  "detail": "Messages cannot be empty"
}
```

### 401 Unauthorized

Returned when authentication fails.

```json
{
  "detail": "Invalid API key"
}
```

### 503 Service Unavailable

Returned when the proxy cannot obtain a VQD token from DuckDuckGo.

```json
{
  "detail": "Failed to obtain VQD token"
}
```

### 504 Gateway Timeout

Returned when the request to DuckDuckGo API times out.

```json
{
  "detail": "Request to DuckDuckGo API timed out"
}
```

---

## Request Examples

### cURL - Non-Streaming

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
  }'
```

### cURL - Streaming

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
  }'
```

### Python - Non-Streaming

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Authorization": "Bearer sk-your-key"},
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False
    }
)
print(response.json()["choices"][0]["message"]["content"])
```

### Python - Streaming

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Authorization": "Bearer sk-your-key"},
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Tell me a joke"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### Python with OpenAI Library

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-key",
    base_url="http://localhost:8000/v1"
)

# Non-streaming
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### JavaScript - Fetch API

```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-your-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: false
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

---

## Rate Limiting

The proxy does not implement rate limiting itself, but DuckDuckGo may rate-limit requests. If you receive a 418 or 429 response:

1. The proxy automatically refreshes the VQD token
2. Wait a few seconds before retrying
3. Consider implementing client-side rate limiting

---

## Compatibility

This API is designed to be compatible with OpenAI's Chat Completions API. Most OpenAI client libraries should work with minimal configuration:

```python
client = OpenAI(
    api_key="your-key",
    base_url="http://localhost:8000/v1"
)
```

---

## Response Times

Typical response times:
- **First token**: 1-3 seconds
- **Streaming**: 100-200ms per chunk
- **Full response**: 3-10 seconds depending on length

---

## Supported Models

| Model ID | Provider | Description |
|----------|----------|-------------|
| `gpt-4o-mini` | OpenAI | Fast, efficient GPT-4o variant |
| `gpt-5-mini` | OpenAI | Latest GPT-5 mini model |
| `claude-3-5-haiku` | Anthropic | Fast Claude model |
| `llama-4-scout` | Meta | Llama 4 Scout model |
| `mistral-small` | Mistral | Small Mistral model |

---

## Version History

### v1.0.0 (Current)
- Initial release
- Support for 5 models
- Streaming and non-streaming responses
- Full OpenAI compatibility
- Custom API key authentication

---

## Support

For issues or questions:
1. Check the README.md
2. Review the QUICKSTART.md
3. Check error messages and logs
4. Refer to troubleshooting section in README.md
