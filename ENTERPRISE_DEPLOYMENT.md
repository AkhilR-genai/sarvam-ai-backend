# Enterprise Deployment Guide

## 🏢 Production Architecture

```
                                    Internet
                                        │
                                        ↓
                                ┌──────────────┐
                                │  Load Balancer│
                                │   (AWS ALB)   │
                                └───────┬───────┘
                                        │
                        ┌───────────────┴───────────────┐
                        ↓                               ↓
                ┌──────────────┐              ┌──────────────┐
                │  Frontend    │              │  Frontend    │
                │  (React/TS)  │              │  (React/TS)  │
                │  CloudFront  │              │  CloudFront  │
                └──────┬───────┘              └──────┬───────┘
                       │                              │
                       └──────────┬───────────────────┘
                                  ↓
                          ┌──────────────┐
                          │   API Gateway│
                          │   (AWS/Kong) │
                          └───────┬───────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  FastAPI     │ │  FastAPI     │ │  FastAPI     │
            │  Instance 1  │ │  Instance 2  │ │  Instance 3  │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ↓                   ↓                   ↓
        ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
        │  PostgreSQL  │    │    Redis     │   │   AWS S3     │
        │   (RDS)      │    │  (ElastiCache│   │ (Recordings) │
        └──────────────┘    └──────────────┘   └──────────────┘
                │
                ↓
        ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
        │  Sarvam AI   │    │    Twilio    │   │  CloudWatch  │
        │     API      │    │     API      │   │  Monitoring  │
        └──────────────┘    └──────────────┘   └──────────────┘
```

## 📋 Pre-requisites

### 1. Get Sarvam AI Access
```bash
# Visit: https://www.sarvam.ai/
# Sign up for API access
# Get your API key from dashboard
# Documentation: https://docs.sarvam.ai/
```

### 2. Set up Twilio Account
```bash
# Visit: https://www.twilio.com/
# Sign up and verify account
# Get: Account SID, Auth Token, Phone Number
# Enable Voice capabilities
# Set up webhooks
```

### 3. Cloud Services
- **AWS Account** (or Azure/GCP)
- **Domain Name** with SSL certificate
- **PostgreSQL Database** (RDS or managed service)
- **Redis Instance** (ElastiCache or managed service)

## 🔧 Configuration Steps

### Step 1: Environment Setup

```bash
cd backend

# Copy and edit environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

Required environment variables:
```env
# Sarvam AI - Get from https://www.sarvam.ai/
SARVAM_AI_API_KEY=sk_sarvam_xxxxxxxxxxxxx
SARVAM_AI_BASE_URL=https://api.sarvam.ai/v1

# Twilio - Get from https://console.twilio.com/
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Your public webhook URL (must be HTTPS)
WEBHOOK_BASE_URL=https://api.yourdomain.com

# Enable real calls
ENABLE_REAL_CALLS=true
USE_SARVAM_AI=true

# Database
DATABASE_URL=postgresql://user:pass@rds-host.amazonaws.com:5432/sarvam_ai

# Redis for caching
REDIS_URL=redis://elasticache-host.amazonaws.com:6379/0

# AWS S3 for recordings
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
S3_BUCKET_NAME=sarvam-ai-prod-recordings
```

### Step 2: Database Setup

```bash
# Install PostgreSQL client
pip install psycopg2-binary sqlalchemy

# Create database schema
python scripts/init_db.py
```

### Step 3: Deploy Backend

#### Option A: Docker Deployment
```bash
# Build Docker image
docker build -t sarvam-ai-backend .

# Run container
docker run -d \
  --name sarvam-backend \
  -p 8000:8000 \
  --env-file .env \
  sarvam-ai-backend
```

#### Option B: Kubernetes
```bash
# Apply k8s manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

#### Option C: AWS Elastic Beanstalk
```bash
eb init -p python-3.11 sarvam-ai-backend
eb create sarvam-ai-prod
eb deploy
```

### Step 4: Configure Twilio Webhooks

Go to Twilio Console → Phone Numbers → Select your number → Configure:

```
Voice & Fax:
  - A CALL COMES IN: Webhook
  - URL: https://api.yourdomain.com/api/twilio/voice/{call_id}
  - HTTP Method: POST

Status Callback:
  - URL: https://api.yourdomain.com/api/twilio/status/{call_id}
  - Events: All

Recording Callback:
  - URL: https://api.yourdomain.com/api/twilio/recording/{call_id}
```

### Step 5: Test Integration

```bash
# Test Sarvam AI connection
curl -X POST https://api.yourdomain.com/api/test/sarvam-ai \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, testing Sarvam AI"}'

# Test Twilio connection
curl -X POST https://api.yourdomain.com/api/test/twilio \
  -H "Content-Type: application/json" \
  -d '{"to": "+919876543210"}'
```

## 🚀 Real Call Flow

### 1. User Initiates Call
```
Frontend → POST /api/real-calls/initiate →
  Backend creates call session →
    Twilio makes outbound call →
      Lead's phone rings
```

### 2. Lead Answers
```
Twilio → Webhook: /api/twilio/voice/{call_id} →
  Backend generates greeting TwiML →
    Sarvam AI TTS: "Hello {name}!" →
      Twilio plays audio to lead
```

### 3. Lead Speaks
```
Lead speaks → Twilio captures audio →
  Webhook: /api/twilio/process-speech/{call_id} →
    Sarvam AI STT: audio → text →
      Sarvam AI LLM: generate response →
        Sarvam AI TTS: text → audio →
          Twilio plays to lead
```

### 4. Conversation Continues
```
Back and forth between AI and lead
Each exchange goes through:
  - Speech Recognition (Sarvam AI)
  - Response Generation (Sarvam AI)
  - Speech Synthesis (Sarvam AI)
  - Real-time updates via WebSocket to frontend
```

### 5. Call Ends
```
Either party hangs up →
  Twilio status webhook →
    Backend saves call data →
      Recording uploaded to S3 →
        Analytics calculated →
          CRM updated
```

## 📊 Monitoring & Analytics

### CloudWatch Dashboards
- API response times
- Error rates
- Call success rates
- Sarvam AI API latency
- Twilio call quality

### Metrics to Track
- Total calls made
- Average call duration
- Conversion rate (deal probability)
- Objection types and frequency
- Response times
- Cost per call

### Alerts Setup
- Failed API calls to Sarvam AI
- Twilio webhook failures
- High error rates
- Slow response times
- Budget thresholds

## 💰 Cost Estimation

### Per Call Costs (approximate)

| Service | Cost | Notes |
|---------|------|-------|
| Twilio Voice | $0.013/min | US outbound |
| Sarvam AI TTS | $0.06/min | Text-to-speech |
| Sarvam AI STT | $0.024/min | Speech-to-text |
| Sarvam AI LLM | $0.002/call | Conversation AI |
| AWS Storage | $0.023/GB | S3 for recordings |
| **Total** | **~$0.12/min** | 5-min call = $0.60 |

### Monthly Estimate (10,000 calls, avg 5 min each)
- Twilio: $650
- Sarvam AI: $4,300
- AWS Infrastructure: $500
- **Total: ~$5,450/month**

## 🔒 Security Best Practices

1. **API Keys**: Store in AWS Secrets Manager
2. **Webhooks**: Validate Twilio signatures
3. **HTTPS Only**: Force SSL/TLS
4. **Rate Limiting**: Prevent abuse
5. **Authentication**: JWT tokens for frontend
6. **GDPR Compliance**: Recording consent
7. **PCI Compliance**: If handling payments
8. **Audit Logs**: Track all API calls

## 📈 Scaling Strategies

### Horizontal Scaling
- Auto-scaling groups (AWS)
- Load balancer distribution
- Stateless backend instances

### Database Optimization
- Read replicas for analytics
- Connection pooling
- Caching with Redis

### Cost Optimization
- Reserved instances
- Spot instances for non-critical tasks
- Batch processing for analytics

## 🐛 Troubleshooting

### Twilio Webhooks Not Working
```bash
# Use ngrok for local testing
ngrok http 8000

# Update Twilio webhook to ngrok URL
https://xxxx.ngrok.io/api/twilio/voice/{call_id}
```

### Sarvam AI API Errors
```bash
# Check API key
echo $SARVAM_AI_API_KEY

# Test endpoint
curl https://api.sarvam.ai/v1/health \
  -H "Authorization: Bearer $SARVAM_AI_API_KEY"
```

### High Latency
- Enable Redis caching
- Use CDN for static assets
- Optimize database queries
- Use async operations

## 📞 Support

- **Sarvam AI Support**: support@sarvam.ai
- **Twilio Support**: https://support.twilio.com
- **Documentation**: See /docs/README.md
