# Quick Start Guide

Get the DuckDuckGo AI Proxy up and running in 5 minutes!

## Option 1: Run Directly (Fastest)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key (optional, has a default)
export DUCKDUCKGO_API_KEY=sk-your-secure-key-here

# 3. Start the server
python app.py
```

Server will be available at `http://localhost:8000`

## Option 2: Run with Docker

```bash
# 1. Build the image
docker build -t duckduckgo-proxy .

# 2. Run the container
docker run -p 8000:8000 \
  -e DUCKDUCKGO_API_KEY=sk-your-secure-key-here \
  duckduckgo-proxy
```

## Option 3: Run with Docker Compose

```bash
# 1. Start the service
docker-compose up -d

# 2. Check logs
docker-compose logs -f
```

## Test the Proxy

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. List Models
```bash
curl -H "Authorization: Bearer sk-your-secure-key-here" \
  http://localhost:8000/v1/models
```

### 3. Simple Chat Request
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-secure-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### 4. Streaming Chat Request
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-secure-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

## Use with Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-secure-key-here",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

print(response.choices[0].message.content)
```

## Available Models

- `gpt-4o-mini` (default)
- `gpt-5-mini`
- `claude-3-5-haiku`
- `llama-4-scout`
- `mistral-small`

## Configuration

Edit `.env` file to customize:
- `DUCKDUCKGO_API_KEY`: Your API key for authentication
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

## Troubleshooting

**Server won't start?**
- Check if port 8000 is available: `lsof -i :8000`
- Try a different port: `PORT=8001 python app.py`

**Getting 401 Unauthorized?**
- Make sure you're sending the correct API key in the Authorization header
- Format: `Authorization: Bearer sk-your-key-here`

**Getting errors from DuckDuckGo?**
- Check your internet connection
- Wait a few seconds and try again (rate limiting)
- Try a different model

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Run the test client: `python test_client.py`
- Deploy to production using Docker
- Integrate with your applications

## Support

For more information, see [README.md](README.md) or check the troubleshooting section.
