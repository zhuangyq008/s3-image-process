import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

from image_processor import resize_image, ResizeMode
from s3_operations import S3Config, get_s3_client, download_image_from_s3, upload_image_to_s3, get_full_s3_key

# Configuration class
class ImageProcessingConfig(BaseModel):
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_formats: list = ["jpg", "jpeg", "png", "webp"]

# Pydantic models
class ResizeRequest(BaseModel):
    image_key: str
    p: Optional[int] = Field(None, ge=1, le=1000, description="Percentage for proportional scaling")
    w: Optional[int] = Field(None, gt=0, description="Target width")
    h: Optional[int] = Field(None, gt=0, description="Target height")
    m: Optional[ResizeMode] = Field(ResizeMode.LFIT, description="Resize mode")

class ResizeResponse(BaseModel):
    resized_image_key: str

# FastAPI app
app = FastAPI()

@app.post("/resize", response_model=ResizeResponse)
async def resize_image_endpoint(request: ResizeRequest):
    s3_config = S3Config()
    s3_client = get_s3_client()

    # Get full S3 key with prefix
    full_image_key = get_full_s3_key(request.image_key)

    # Download image from S3
    image_data = download_image_from_s3(s3_client, s3_config.bucket_name, full_image_key)

    # Prepare resize parameters
    resize_params = {k: v for k, v in request.dict().items() if v is not None and k != 'image_key'}

    # Resize image
    resized_image_data = resize_image(image_data, resize_params)

    # Generate new key for resized image
    file_name, file_extension = os.path.splitext(request.image_key)
    resize_info = f"_resized_{request.p}p" if request.p else f"_resized_{request.w}x{request.h}_{request.m}"
    resized_image_key = f"{file_name}{resize_info}{file_extension}"

    # Get full S3 key for resized image
    full_resized_image_key = get_full_s3_key(resized_image_key)

    # Upload resized image to S3
    upload_image_to_s3(s3_client, s3_config.bucket_name, full_resized_image_key, resized_image_data)

    return ResizeResponse(resized_image_key=resized_image_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
