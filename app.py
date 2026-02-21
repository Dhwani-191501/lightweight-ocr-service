import os
import io
import base64
import json
import requests
from typing import Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import pytesseract
from pytesseract import image_to_string

app = FastAPI(
    title="Lightweight OCR Service",
    description="Receives screenshots directly, extracts text, and sends to misinfo detector",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MISINFO_DETECTOR_URL = os.getenv("MISINFO_DETECTOR_URL", "http://localhost:8000")

class ImageDataRequest(BaseModel):
    image_data: str  # base64 encoded image
    source: Optional[str] = None

class S3NotificationRequest(BaseModel):
    # S3 sends this format when configured to send object data
    image_data: str  # base64 encoded image from S3
    bucket: str
    key: str
    event_time: Optional[str] = None

class TextExtractionRequest(BaseModel):
    image_data: str  # base64 encoded image

class FactCheckResponse(BaseModel):
    results: list
    extracted_text: str
    source: str

def extract_text_from_image(image_data: bytes) -> str:
    """Extract text from image bytes using Tesseract OCR"""
    try:
        image = Image.open(io.BytesIO(image_data))
        text = image_to_string(image)
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

def send_to_misinfo_detector(text: str) -> dict:
    """Send extracted text to misinfo detector"""
    try:
        response = requests.post(
            f"{MISINFO_DETECTOR_URL}/fact-check",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # For Railway deployment, return error instead of raising exception
        print(f"❌ Failed to connect to misinfo detector: {str(e)}")
        return {"error": f"Failed to connect to misinfo detector: {str(e)}"}
    except Exception as e:
        print(f"❌ Error sending to misinfo detector: {str(e)}")
        return {"error": f"Error: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Lightweight OCR Service is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if misinfo detector is accessible
        response = requests.get(f"{MISINFO_DETECTOR_URL}/", timeout=5)
        detector_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        detector_status = "unreachable"
    
    return {
        "status": "healthy",
        "misinfo_detector": detector_status,
        "ocr_engine": "tesseract",
        "aws_credentials": "not_required"
    }

@app.post("/upload-image", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    """Upload image file directly and extract text, then send to misinfo detector"""
    try:
        # Read uploaded file
        image_data = await file.read()
        
        # Extract text
        extracted_text = extract_text_from_image(image_data)
        
        print(f"\n🔍 Extracted Text: '{extracted_text}'")
        print(f"📤 Sending to misinfo detector at {MISINFO_DETECTOR_URL}")
        
        # Send to misinfo detector
        if extracted_text.strip():
            fact_check_results = send_to_misinfo_detector(extracted_text)
            print(f"✅ Misinfo detector response: {fact_check_results}")
        else:
            fact_check_results = {"error": "No text extracted"}
            print("⚠️  No text extracted from image")
        
        return {
            "extracted_text": extracted_text,
            "status": "success",
            "text_length": len(extracted_text),
            "filename": file.filename,
            "content_type": file.content_type,
            "fact_check_results": fact_check_results
        }
        
    except Exception as e:
        print(f"❌ Image processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@app.post("/process-s3-notification", response_model=FactCheckResponse)
async def process_s3_notification(request: S3NotificationRequest):
    """Process S3 notification that includes image data"""
    try:
        # Decode base64 image from S3 notification
        image_data = base64.b64decode(request.image_data)
        
        # Extract text
        extracted_text = extract_text_from_image(image_data)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Send to misinfo detector
        fact_check_results = send_to_misinfo_detector(extracted_text)
        
        return FactCheckResponse(
            results=fact_check_results.get("results", []),
            extracted_text=extracted_text,
            source=f"s3://{request.bucket}/{request.key}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-image-data", response_model=FactCheckResponse)
async def process_image_data(request: ImageDataRequest):
    """Process base64 encoded image data directly"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_data)
        extracted_text = extract_text_from_image(image_data)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Send to misinfo detector
        fact_check_results = send_to_misinfo_detector(extracted_text)
        
        return FactCheckResponse(
            results=fact_check_results.get("results", []),
            extracted_text=extracted_text,
            source=request.source or "direct_upload"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/extract-text-only")
async def extract_text_only(request: TextExtractionRequest):
    """Extract text from base64 encoded image without fact checking"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_data)
        extracted_text = extract_text_from_image(image_data)
        
        return {
            "extracted_text": extracted_text,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

@app.post("/fact-check-text")
async def fact_check_text(text: str):
    """Fact check provided text without image processing"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        fact_check_results = send_to_misinfo_detector(text)
        
        return {
            "results": fact_check_results.get("results", []),
            "input_text": text,
            "source": "direct_text_input"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact checking failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
