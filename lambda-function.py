import json
import base64
import boto3
import os
import requests

# Environment variables
RAILWAY_URL = os.environ['RAILWAY_URL']

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function triggered by S3 upload.
    Reads the image and forwards it to Railway OCR service.
    """
    
    try:
        # Extract S3 event information
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            # Skip if this is a folder or not an image
            if not object_key.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                print(f"Skipping non-image file: {object_key}")
                continue
            
            # Download image from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            image_data = response['Body'].read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Send to Railway
            railway_payload = {
                "image_data": image_base64,
                "bucket": bucket_name,
                "key": object_key
            }
            
            railway_response = requests.post(
                f"{RAILWAY_URL}/process-s3-notification",
                json=railway_payload,
                timeout=30
            )
            
            if railway_response.status_code == 200:
                print(f"Successfully processed {object_key}")
                print(f"Response: {railway_response.json()}")
            else:
                print(f"Failed to process {object_key}: {railway_response.status_code}")
                print(f"Error: {railway_response.text}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Processing complete')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
