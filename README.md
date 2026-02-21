# Lightweight OCR Service

A lightweight FastAPI service that receives screenshots from S3, extracts text using Tesseract OCR, and sends the extracted text to your local misinfo detector.

## Features

- **S3 Integration**: Directly processes images from S3 buckets
- **OCR Processing**: Uses Tesseract for text extraction
- **Misinfo Detection**: Forwards extracted text to local misinfo detector
- **Multiple Input Methods**: S3 events, image URLs, base64 images
- **Health Checks**: Monitor service and misinfo detector status
- **Docker Support**: Easy deployment with Docker/Docker Compose

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials and local misinfo detector URL
```

### 2. Run with Docker Compose

```bash
# Build and run
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Run Locally (for development)

```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (macOS)
brew install tesseract tesseract-lang

# Install Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Run the service
python app.py
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Process S3 Screenshot
```bash
POST /process-s3-screenshot
Content-Type: application/json

{
  "bucket": "your-s3-bucket",
  "key": "path/to/screenshot.png",
  "region": "us-east-1"  # optional
}
```

### Process Image from URL
```bash
POST /process-image-url
Content-Type: application/json

{
  "image_url": "https://example.com/screenshot.png"
}
```

### Extract Text Only (no fact checking)
```bash
POST /extract-text-only
Content-Type: application/json

{
  "image_data": "base64-encoded-image-data"
}
```

### Fact Check Text Directly
```bash
POST /fact-check-text
Content-Type: application/json

{
  "text": "This is a claim to fact check"
}
```

## Railway Deployment (Recommended)

### 1. Create GitHub Repository
```bash
# Initialize git and push to GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/lightweight-ocr-service.git
git push -u origin main
```

### 2. Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect and deploy your service

### 3. Configure Environment Variables
In Railway dashboard, add these environment variables:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key  
- `AWS_REGION` - Your AWS region (e.g., `us-east-1`)
- `MISINFO_DETECTOR_URL` - Your local detector URL (use ngrok for public access)

### 4. Get Your Railway URL
After deployment, Railway will give you a URL like:
```
https://your-service-name.up.railway.app
```

## S3 Integration Setup

### Option 1: S3 Event Notifications (Recommended)
1. Go to your S3 bucket in AWS Console
2. Under "Properties" → "Event notifications"
3. Create a new notification with:
   - **Event types**: `s3:ObjectCreated:*`
   - **Destination**: Amazon SNS topic
   - **Endpoint**: Your Railway URL + `/process-s3-screenshot`

### Option 2: S3 → Lambda → Railway
Create a Lambda function that triggers on S3 uploads and calls your Railway service:

```python
import json
import requests
import os

RAILWAY_URL = os.environ['RAILWAY_URL']

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Call your Railway service
        response = requests.post(
            f'{RAILWAY_URL}/process-s3-screenshot',
            json={'bucket': bucket, 'key': key},
            timeout=30
        )
        
    return {'statusCode': 200}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | - | AWS secret key |
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `MISINFO_DETECTOR_URL` | No | `http://localhost:8000` | Local misinfo detector URL |

## Response Format

```json
{
  "results": [
    {
      "claim": "Extracted claim text",
      "verdict": "SUPPORTED|REFUTED|INSUFFICIENT",
      "scores": {...},
      "citations": ["url1", "url2"]
    }
  ],
  "extracted_text": "Full text extracted from image",
  "source": "s3://bucket/key or image_url"
}
```

## Deployment Options

### AWS Lambda
```bash
# Build for Lambda
docker build -t ocr-lambda .

# Deploy using AWS CLI or Serverless Framework
```

### AWS ECS/Fargate
```bash
# Push to ECR
aws ecr create-repository --repository-name lightweight-ocr-service
docker tag ocr-service:latest <account>.dkr.ecr.<region>.amazonaws.com/lightweight-ocr-service
docker push <account>.dkr.ecr.<region>.amazonaws.com/lightweight-ocr-service
```

### Local Development
```bash
# Run with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

## Monitoring

- Health check endpoint: `/health`
- Service logs available in container logs
- Misinfo detector connectivity status in health checks

## Security Notes

- Store AWS credentials securely (use IAM roles when possible)
- Restrict S3 bucket access to specific prefixes
- Consider adding authentication for production deployments
- Validate image file types and sizes before processing
