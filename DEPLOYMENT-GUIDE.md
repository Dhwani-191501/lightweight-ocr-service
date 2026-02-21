# Complete Deployment Guide

## Overview
S3 → Lambda → Railway → Local Misinfo Detector (via ngrok)

## Step 1: Railway Setup

### 1.1 Deploy to Railway
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/lightweight-ocr-service.git
git push -u origin main
```

### 1.2 Railway Environment Variables
In Railway dashboard, set ONLY:
```
MISINFO_DETECTOR_URL=https://your-ngrok-url.ngrok-free.app
```

### 1.3 Get Railway URL
After deployment, Railway gives you:
```
https://your-service-name.up.railway.app
```

## Step 2: Local Setup

### 2.1 Start Your Misinfo Detector
```bash
cd /Users/mehakgoel/Desktop/Model/misinfo_detector
python api.py
```

### 2.2 Setup ngrok
```bash
ngrok http 8000
```
Copy the ngrok URL and update Railway environment variable.

## Step 3: AWS Setup

### 3.1 Create Lambda Function
1. Go to AWS Lambda → Create function
2. **Function name**: `s3-to-railway-ocr`
3. **Runtime**: Python 3.11
4. **Architecture**: x86_64
5. Click "Create function"

### 3.2 Lambda Configuration
1. **Code**: Copy contents of `lambda-function.py`
2. **Runtime**: Python 3.11
3. **Handler**: `lambda_function.lambda_handler`

### 3.3 Lambda Environment Variables
```
RAILWAY_URL=https://your-service-name.up.railway.app
```

### 3.4 Lambda Permissions
1. Go to "Configuration" → "Permissions"
2. Click on the role name
3. Add these policies:
   - `AmazonS3ReadOnlyAccess` (to read from S3)
   - `AWSLambdaBasicExecutionRole` (for logging)

### 3.5 Lambda Timeout
1. Go to "Configuration" → "General configuration"
2. Set **Timeout** to 30 seconds

## Step 4: S3 Setup

### 4.1 Create S3 Bucket
1. Go to S3 → Create bucket
2. **Bucket name**: unique-name-screenshots
3. **Region**: same as Lambda
4. Keep defaults, create bucket

### 4.2 S3 Event Notification
1. Go to your bucket → "Properties" → "Event notifications"
2. Click "Create event notification"
3. **Event name**: `trigger-ocr`
4. **Event types**: `s3:ObjectCreated:*`
5. **Destination**: Choose "Lambda function"
6. **Lambda function**: `s3-to-railway-ocr`
7. Click "Create changes"

## Step 5: Test

### 5.1 Upload Test Image
```bash
# Upload any screenshot to your S3 bucket
aws s3 cp test-image.png s3://your-bucket-name/
```

### 5.2 Check Logs
1. **Lambda logs**: CloudWatch → Log groups → `/aws/lambda/s3-to-railway-ocr`
2. **Railway logs**: Railway dashboard → Logs

## File Structure After Cleanup
```
lightweight-ocr-service/
├── app.py                    # Main Railway service
├── requirements.txt          # Python dependencies (no AWS)
├── railway.toml             # Railway configuration
├── .gitignore               # Git ignore file
├── lambda-function.py       # AWS Lambda function
├── DEPLOYMENT-GUIDE.md      # This guide
├── ngrok-setup.md          # ngrok instructions
└── README.md               # Updated README
```

## Environment Variables Summary

### Railway (1 variable):
- `MISINFO_DETECTOR_URL=https://your-ngrok-url.ngrok-free.app`

### Lambda (1 variable):
- `RAILWAY_URL=https://your-service-name.up.railway.app`

### AWS Credentials Needed:
- Only for Lambda role permissions (S3 read access)
- NOT needed on Railway

## Flow Summary
1. Screenshot uploaded to S3
2. S3 triggers Lambda
3. Lambda reads image, converts to base64
4. Lambda sends to Railway
5. Railway extracts text via OCR
6. Railway sends text to your local misinfo detector
7. Results returned

## Costs
- **Railway**: Free tier (500 hours/month)
- **Lambda**: Free tier (1M requests/month)
- **S3**: Free tier (5GB storage, 20K requests/month)
- **ngrok**: Free (with URL changes)
