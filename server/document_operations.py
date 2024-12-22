import os
from typing import BinaryIO, List
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from s3_operations import S3Config, get_s3_client, download_image_from_s3

def get_document_from_s3(client, bucket: str, key: str) -> bytes:
    """
    Download document from S3 using the same method as image download
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: Object key in S3
        
    Returns:
        bytes: Document data
        
    Raises:
        HTTPException: If document not found or bucket not configured
    """
    # 使用相同的下载函数，因为它已经被证明是可用的
    return download_image_from_s3(client, bucket, key)

def upload_document_to_s3(client, bucket: str, key: str, data: bytes, content_type: str = None):
    """
    Upload document to S3
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: Object key in S3
        data: Document bytes to upload
        content_type: Optional MIME type
        
    Raises:
        HTTPException: If upload fails or bucket not configured
    """
    if not bucket:
        raise HTTPException(
            status_code=500,
            detail="S3 bucket not configured. Set S3_BUCKET_NAME environment variable."
        )
    
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            **extra_args
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

def upload_multiple_files_to_s3(
    client,
    bucket: str,
    base_prefix: str,
    files: List[tuple[str, bytes, str]]
):
    """
    Upload multiple files to S3
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        base_prefix: Base S3 prefix for uploads
        files: List of tuples containing (filename, file_data, content_type)
    """
    for filename, file_data, content_type in files:
        key = os.path.join(base_prefix, filename)
        upload_document_to_s3(client, bucket, key, file_data, content_type)

def get_mime_type(format_str: str) -> str:
    """Get the correct MIME type for a given format"""
    mime_types = {
        # Documents
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'wps': 'application/vnd.ms-works',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf',
        # Images
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        # Text
        'txt': 'text/plain'
    }
    return mime_types.get(format_str.lower(), 'application/octet-stream')
