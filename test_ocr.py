import base64
import requests
import io
from PIL import Image, ImageDraw, ImageFont

def create_test_image(text="Hello World! This is a test."):
    """Create a simple test image with text"""
    # Create a white image
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((10, 10), text, fill='black', font=font)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def test_ocr_locally():
    """Test OCR extraction locally"""
    print("🧪 Testing OCR Service Locally")
    print("=" * 50)
    
    # Start the OCR service first (in another terminal)
    # python test-app.py
    
    # Create test image
    test_text = "COVID-19 vaccines are safe and effective. They prevent severe illness."
    print(f"📝 Creating test image with text: '{test_text}'")
    
    image_data = create_test_image(test_text)
    
    # Test the OCR service
    url = "http://localhost:8080/extract-text-only"
    
    payload = {
        "image_data": image_data
    }
    
    try:
        print("🔄 Sending request to OCR service...")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OCR Test Successful!")
            print(f"Original text: '{test_text}'")
            print(f"Extracted text: '{result['extracted_text']}'")
            print(f"Text length: {result['text_length']}")
            
            # Check if extraction worked
            if result['extracted_text'].strip():
                print("🎉 Text extraction working!")
            else:
                print("⚠️  No text extracted - check Tesseract installation")
        else:
            print(f"❌ OCR Test Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to OCR service")
        print("💡 Make sure to run: python test-app.py")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def test_health_check():
    """Test health check endpoint"""
    print("\n🏥 Testing Health Check")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting OCR Tests")
    print("Make sure to run 'python test-app.py' in another terminal first!")
    print()
    
    test_health_check()
    test_ocr_locally()
