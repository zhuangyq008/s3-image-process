import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

from image_processor import resize_image, ResizeMode
from s3_operations import S3Config, get_s3_client, download_image_from_s3, upload_image_to_s3

# Configuration class
class ImageProcessingConfig(BaseModel):
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_formats: list = ["jpg", "jpeg", "png", "webp"]

# Pydantic models
class ResizeResponse(BaseModel):
    resized_image_key: str

# FastAPI app
app = FastAPI()

@app.get("/resize/{image_key}", response_model=ResizeResponse)
async def resize_image_endpoint(
    image_key: str,
    p: Optional[int] = Field(None, ge=1, le=1000, description="Percentage for proportional scaling"),
    w: Optional[int] = Field(None, gt=0, description="Target width"),
    h: Optional[int] = Field(None, gt=0, description="Target height"),
    m: Optional[ResizeMode] = Field(ResizeMode.LFIT, description="Resize mode")
):
    s3_config = S3Config()
    s3_client = get_s3_client()

    # Download image from S3
    image_data = download_image_from_s3(s3_client, s3_config.bucket_name, image_key)

    # Prepare resize parameters
    resize_params = {
        "p": p,
        "w": w,
        "h": h,
        "m": m
    }
    resize_params = {k: v for k, v in resize_params.items() if v is not None}

    # Resize image
    resized_image_data = resize_image(image_data, resize_params)

    # Generate new key for resized image
    file_name, file_extension = os.path.splitext(image_key)
    resize_info = f"_resized_{p}p" if p else f"_resized_{w}x{h}_{m}"
    resized_image_key = f"{file_name}{resize_info}{file_extension}"

    # Upload resized image to S3
    upload_image_to_s3(s3_client, s3_config.bucket_name, resized_image_key, resized_image_data)

    return ResizeResponse(resized_image_key=resized_image_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
