# Deployment Guide

Complete guide for deploying the DuckDuckGo AI Proxy to production environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Systemd Service](#systemd-service)
4. [Nginx Reverse Proxy](#nginx-reverse-proxy)
5. [Cloud Platforms](#cloud-platforms)
6. [Security Hardening](#security-hardening)
7. [Monitoring and Logging](#monitoring-and-logging)

---

## Local Development

### Setup

```bash
# Clone the repository
cd /home/ubuntu/duckduckgo-ai-proxy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.sample .env
# Edit .env with your settings
nano .env
```

### Running

```bash
python app.py
```

The server will start on `http://localhost:8000`

### Testing

```bash
# In another terminal
python test_client.py
```

---

## Docker Deployment

### Build Image

```bash
docker build -t duckduckgo-proxy:latest .
```

### Run Container

```bash
docker run -d \
  --name duckduckgo-proxy \
  -p 8000:8000 \
  -e DUCKDUCKGO_API_KEY=sk-your-secure-key \
  --restart unless-stopped \
  duckduckgo-proxy:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Container Management

```bash
# View running containers
docker ps

# View logs
docker logs duckduckgo-proxy

# Follow logs in real-time
docker logs -f duckduckgo-proxy

# Stop container
docker stop duckduckgo-proxy

# Start container
docker start duckduckgo-proxy

# Remove container
docker rm duckduckgo-proxy
```

---

## Systemd Service

### Create Service File

Create `/etc/systemd/system/duckduckgo-proxy.service`:

```ini
[Unit]
Description=DuckDuckGo AI Proxy
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/duckduckgo-ai-proxy

# Environment
EnvironmentFile=/home/ubuntu/duckduckgo-ai-proxy/.env
Environment="PATH=/home/ubuntu/duckduckgo-ai-proxy/venv/bin"

# Start command
ExecStart=/home/ubuntu/duckduckgo-ai-proxy/venv/bin/python app.py

# Restart policy
Restart=on-failure
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Process management
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# Resource limits (optional)
MemoryLimit=512M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=duckduckgo-proxy

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable duckduckgo-proxy

# Start service
sudo systemctl start duckduckgo-proxy

# Check status
sudo systemctl status duckduckgo-proxy

# View logs
sudo journalctl -u duckduckgo-proxy -f
```

### Service Management

```bash
# Stop service
sudo systemctl stop duckduckgo-proxy

# Restart service
sudo systemctl restart duckduckgo-proxy

# Reload configuration
sudo systemctl reload duckduckgo-proxy

# Check service status
sudo systemctl status duckduckgo-proxy

# View recent logs
sudo journalctl -u duckduckgo-proxy -n 50
```

---

## Nginx Reverse Proxy

### Install Nginx

```bash
sudo apt-get update
sudo apt-get install nginx
```

### Configure Nginx

Create `/etc/nginx/sites-available/duckduckgo-proxy`:

```nginx
upstream duckduckgo_proxy {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/duckduckgo-proxy-access.log;
    error_log /var/log/nginx/duckduckgo-proxy-error.log;

    # Proxy configuration
    location / {
        proxy_pass http://duckduckgo_proxy;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 3600;
        proxy_connect_timeout 60;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
}
```

### Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/duckduckgo-proxy \
  /etc/nginx/sites-enabled/duckduckgo-proxy

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Cloud Platforms

### AWS EC2

1. **Launch Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.micro or higher
   - Security group: Allow ports 80, 443, 22

2. **Connect and Setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Update system
   sudo apt-get update && sudo apt-get upgrade -y
   
   # Install dependencies
   sudo apt-get install -y python3-pip python3-venv git
   
   # Clone repository
   git clone https://github.com/your-repo/duckduckgo-proxy.git
   cd duckduckgo-proxy
   
   # Setup and run
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Create systemd service (see above)
   ```

3. **Elastic IP**: Assign static IP address
4. **Load Balancer**: Use ALB for multiple instances

### Google Cloud Platform

1. **Create Compute Instance**
   ```bash
   gcloud compute instances create duckduckgo-proxy \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-micro \
     --zone=us-central1-a
   ```

2. **SSH and Setup**
   ```bash
   gcloud compute ssh duckduckgo-proxy --zone=us-central1-a
   # Follow same setup as AWS above
   ```

### DigitalOcean

1. **Create Droplet**
   - Image: Ubuntu 22.04
   - Size: Basic ($5/month)
   - Region: Closest to you

2. **SSH and Setup**
   ```bash
   ssh root@your-droplet-ip
   # Follow same setup as AWS above
   ```

### Heroku

```bash
# Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set DUCKDUCKGO_API_KEY=sk-your-key

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

---

## Security Hardening

### 1. API Key Management

```bash
# Generate strong API key
openssl rand -hex 32

# Store securely
export DUCKDUCKGO_API_KEY=$(openssl rand -hex 32)

# Use secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
```

### 2. Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# AWS Security Group
# Inbound: SSH (22), HTTP (80), HTTPS (443)
# Outbound: All traffic
```

### 3. HTTPS Only

- Always use HTTPS in production
- Use Let's Encrypt for free SSL certificates
- Redirect HTTP to HTTPS

### 4. Rate Limiting

Configure in Nginx or use middleware:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

### 5. Authentication

- Change default API key
- Use strong, random keys
- Rotate keys regularly
- Consider API key versioning

### 6. Monitoring

- Set up alerts for errors
- Monitor resource usage
- Track API usage patterns
- Log all requests

---

## Monitoring and Logging

### Application Logs

```bash
# View application logs
tail -f /var/log/duckduckgo-proxy.log

# With systemd
sudo journalctl -u duckduckgo-proxy -f
```

### Nginx Logs

```bash
# Access logs
tail -f /var/log/nginx/duckduckgo-proxy-access.log

# Error logs
tail -f /var/log/nginx/duckduckgo-proxy-error.log
```

### Health Monitoring

```bash
# Check health endpoint
curl http://localhost:8000/health

# Automated monitoring
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

### Performance Monitoring

```bash
# CPU and Memory
top
htop

# Disk usage
df -h

# Network
netstat -an | grep 8000
```

### Log Aggregation

Consider using:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **DataDog**
- **New Relic**
- **CloudWatch** (AWS)

### Alerting

Set up alerts for:
- High error rates
- High response times
- Resource exhaustion
- Service downtime

---

## Performance Tuning

### Uvicorn Workers

```bash
# Multiple workers for better throughput
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Connection Pooling

The application uses httpx with connection pooling. Adjust if needed:

```python
# In app.py
async with httpx.AsyncClient(
    timeout=60.0,
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=100)
) as client:
    ...
```

### Caching

Consider implementing caching for:
- VQD tokens (already done)
- Common queries
- Model list

### Database

For production, consider:
- Caching responses
- Storing conversation history
- Analytics

---

## Backup and Recovery

### Backup Strategy

```bash
# Backup configuration
tar -czf duckduckgo-proxy-backup-$(date +%Y%m%d).tar.gz \
  /home/ubuntu/duckduckgo-ai-proxy/.env \
  /home/ubuntu/duckduckgo-ai-proxy/

# Store in S3, GCS, or other backup service
```

### Recovery

```bash
# Restore from backup
tar -xzf duckduckgo-proxy-backup-20240115.tar.gz -C /
sudo systemctl restart duckduckgo-proxy
```

---

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Use Nginx, HAProxy, or cloud load balancer
2. **Multiple Instances**: Run multiple proxy servers
3. **Session Management**: Ensure VQD tokens are shared or refreshed per instance

### Vertical Scaling

1. **Increase Resources**: More CPU, RAM
2. **Optimize Code**: Profile and optimize bottlenecks
3. **Connection Pooling**: Tune connection limits

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u duckduckgo-proxy -n 50

# Check port availability
sudo lsof -i :8000

# Check permissions
ls -la /home/ubuntu/duckduckgo-ai-proxy/
```

### High Memory Usage

```bash
# Check process memory
ps aux | grep python

# Limit memory in systemd
MemoryLimit=512M
```

### Connection Timeouts

- Increase timeout in code
- Check network connectivity
- Verify DuckDuckGo API is accessible

---

## Support

For deployment issues:
1. Check logs first
2. Verify configuration
3. Test connectivity to DuckDuckGo
4. Review security settings
5. Check resource availability
