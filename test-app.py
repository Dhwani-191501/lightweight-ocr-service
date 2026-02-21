import os
import io
import base64
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from PIL import Image
import pytesseract
from pytesseract import image_to_string

app = FastAPI(
    title="Lightweight OCR Service - Test Mode",
    description="Test OCR extraction without misinfo detector",
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

class TextExtractionRequest(BaseModel):
    image_data: str  # base64 encoded image

def extract_text_from_image(image_data: bytes) -> str:
    """Extract text from image bytes using Tesseract OCR"""
    try:
        image = Image.open(io.BytesIO(image_data))
        text = image_to_string(image)
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

def send_to_misinfo_detector(text: str) -> dict:
    """Send extracted text to local misinfo detector"""
    try:
        import requests
        response = requests.post(
            f"{MISINFO_DETECTOR_URL}/fact-check",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to misinfo detector: {str(e)}")
        return {"error": f"Failed to connect to misinfo detector: {str(e)}"}
    except Exception as e:
        print(f"❌ Error sending to misinfo detector: {str(e)}")
        return {"error": f"Error: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Lightweight OCR Service - Test Mode is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ocr_engine": "tesseract",
        "mode": "test"
    }

@app.post("/extract-text-only")
async def extract_text_only(request: TextExtractionRequest):
    """Extract text from base64 encoded image without fact checking"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_data)
        extracted_text = extract_text_from_image(image_data)
        
        return {
            "extracted_text": extracted_text,
            "status": "success",
            "text_length": len(extracted_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

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

@app.post("/process-image-data")
async def process_image_data(request: ImageDataRequest):
    """Process base64 encoded image data directly"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_data)
        extracted_text = extract_text_from_image(image_data)
        
        return {
            "extracted_text": extracted_text,
            "status": "success",
            "source": request.source or "direct_upload",
            "text_length": len(extracted_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple web interface for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCR Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }
            .error { background: #f8d7da; color: #721c24; }
            .success { background: #d4edda; color: #155724; }
        </style>
    </head>
    <body>
        <h1>🔍 OCR Test Interface</h1>
        <p>Upload an image to extract text</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <input type="file" id="fileInput" name="file" accept="image/*" required>
                <p>📁 Click to select an image</p>
            </div>
            <button type="submit">🔍 Extract Text</button>
        </form>
        
        <div id="result"></div>
        
        <script>
            const uploadForm = document.getElementById('uploadForm');
            const fileInput = document.getElementById('fileInput');
            const result = document.getElementById('result');
            
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch('/upload-image', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        result.innerHTML = `
                            <div class="result success">
                                <h3>✅ Success</h3>
                                <p><strong>File:</strong> ${data.filename}</p>
                                <p><strong>Extracted Text:</strong></p>
                                <p style="background: white; padding: 10px; border-radius: 3px;">${data.extracted_text || 'No text found'}</p>
                                <p><strong>Characters:</strong> ${data.text_length}</p>
                            </div>
                        `;
                    } else {
                        result.innerHTML = `
                            <div class="result error">
                                <h3>❌ Error</h3>
                                <p>${data.detail}</p>
                            </div>
                        `;
                    }
                } catch (error) {
                    result.innerHTML = `
                        <div class="result error">
                            <h3>❌ Error</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
