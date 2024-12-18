import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from pydantic import BaseModel, Field
import os

class S3Config(BaseModel):
    region_name: str = Field(default=os.getenv("AWS_REGION", "us-east-1"))
    bucket_name: str = Field(
        default=os.getenv("S3_BUCKET_NAME"),
        description="S3 bucket name is required. Set S3_BUCKET_NAME environment variable."
    )
    image_prefix: str = Field(default=os.getenv("S3_IMAGE_PREFIX", ""))

    def __init__(self, **data):
        super().__init__(**data)
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable must be set")

def get_s3_client():
    """Get S3 client with configured region"""
    config = S3Config()
    return boto3.client(
        's3',
        region_name=config.region_name
    )

def download_image_from_s3(client, bucket, key):
    """
    Download image from S3
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: Object key in S3
        
    Returns:
        bytes: Image data
        
    Raises:
        HTTPException: If image not found or bucket not configured
    """
    if not bucket:
        raise HTTPException(
            status_code=500,
            detail="S3 bucket not configured. Set S3_BUCKET_NAME environment variable."
        )
    
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"Image not found: {key}")
        elif e.response['Error']['Code'] == 'NoSuchBucket':
            raise HTTPException(status_code=500, detail=f"Bucket not found: {bucket}")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

def upload_image_to_s3(client, bucket, key, image_data):
    """
    Upload image to S3
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: Object key in S3
        image_data: Image bytes to upload
        
    Raises:
        HTTPException: If upload fails or bucket not configured
    """
    if not bucket:
        raise HTTPException(
            status_code=500,
            detail="S3 bucket not configured. Set S3_BUCKET_NAME environment variable."
        )
    
    try:
        client.put_object(Bucket=bucket, Key=key, Body=image_data)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

def get_full_s3_key(image_key: str) -> str:
    """Get full S3 key including prefix if configured"""
    config = S3Config()
    return os.path.join(config.image_prefix, image_key)
