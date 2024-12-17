import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from pydantic import BaseModel
import os

class S3Config(BaseModel):
    region_name: str = os.getenv("AWS_REGION", "us-east-1")
    bucket_name: str = os.getenv("S3_BUCKET_NAME")
    image_prefix: str = os.getenv("S3_IMAGE_PREFIX", "")  # New field with default empty string

def get_s3_client():
    config = S3Config()
    return boto3.client(
        's3',
        region_name=config.region_name
    )

def download_image_from_s3(client, bucket, key):
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except ClientError as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {e}")

def upload_image_to_s3(client, bucket, key, image_data):
    try:
        client.put_object(Bucket=bucket, Key=key, Body=image_data)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")

def get_full_s3_key(image_key: str) -> str:
    config = S3Config()
    return os.path.join(config.image_prefix, image_key)
