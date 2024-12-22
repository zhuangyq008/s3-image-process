import os
import hashlib
import asyncio
from fastapi import FastAPI, Query, status, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from PIL import Image
import io

# Import existing image processing modules
from image_resizer import resize_image, ResizeMode
from image_cropper import crop_image, CropGravity
from s3_operations import S3Config, get_s3_client, download_image_from_s3
from watermark import add_watermark
from image_format_converter import convert_format, ImageFormat
from auto_orient import auto_orient_image
from quality import transform_quality

# Import new document conversion modules
from document_converter import (
    document_converter,
    InputFormat,
    OutputFormat,
    ConversionStatus,
    ConversionTask
)
from document_operations import (
    get_document_from_s3,
    upload_document_to_s3,
    upload_multiple_files_to_s3,
    get_mime_type
)
from format_handlers import get_handler

# Configuration classes
class ImageProcessingConfig(BaseModel):
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_formats: list = ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"]

class DocumentConversionConfig(BaseModel):
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    image_dpi: int = 300

# Request/Response models for document conversion
class ConversionRequest(BaseModel):
    input_key: str
    input_format: InputFormat
    output_format: OutputFormat
    output_prefix: str
    image_dpi: Optional[int] = 300

class ConversionResponse(BaseModel):
    task_id: str
    status: ConversionStatus
    message: str

# FastAPI app
app = FastAPI()

# Existing image processing functions
def parse_operation(operation_str: str) -> tuple[str, dict]:
    """Parse operation string like 'resize,p_50' or 'format,png' into (operation, params)"""
    parts = operation_str.split(',')
    operation = parts[0]
    params = {}
    
    for param in parts[1:]:
        if operation == 'auto-orient':
            # Special handling for auto-orient parameter
            try:
                params['auto'] = int(param)
            except ValueError:
                raise ValueError("auto-orient parameter must be 0 or 1")
        elif '_' in param:
            key, value = param.split('_')
            # Keep color and text as strings, try to convert others to int
            if key not in {'color', 'text'}:
                try:
                    value = int(value)
                except ValueError:
                    pass
            params[key] = value
        else:
            # Handle direct format specification (e.g., 'format,png' instead of 'format,f_png')
            if operation == 'format':
                params['f'] = param
    
    return operation, params

def get_content_type(format_str: str) -> str:
    """Get the correct content type for a given format"""
    format_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'gif': 'image/gif',
        'tiff': 'image/tiff'
    }
    return format_map.get(format_str.lower(), 'image/jpeg')

# Existing image processing endpoints
@app.get("/image/{image_key}")
async def process_image(
    image_key: str,
    operations: Optional[str] = Query(None, description="Chained operations, e.g., resize,p_50/crop,w_200,h_200")
):
    """
    Process an image with chained operations.
    Example: /image/example.jpg?operations=resize,p_50/crop,w_200,h_200/watermark,text_Copyright,g_se/format,png
    """
    try:
        s3_config = S3Config()
        s3_client = get_s3_client()

        # Download image from S3
        image_data = download_image_from_s3(s3_client, s3_config.bucket_name, image_key)
        current_image_data = image_data
        content_type = None

        # Process operations if provided
        if operations:
            # Split and process operations
            operation_chain = [op for op in operations.split('/') if op]
            
            for operation_str in operation_chain:
                operation, params = parse_operation(operation_str)
                
                if operation == 'auto-orient':
                    orient_params = {
                        'auto': params.get('auto', 0)
                    }
                    current_image_data = auto_orient_image(current_image_data, orient_params)
                
                elif operation == 'resize':
                    resize_params = {}
                    if 'p' in params:
                        resize_params['p'] = params['p']
                    if 'w' in params:
                        resize_params['w'] = params['w']
                    if 'h' in params:
                        resize_params['h'] = params['h']
                    if 'm' in params:
                        resize_params['m'] = ResizeMode(params['m'])
                    current_image_data = resize_image(current_image_data, resize_params)
                    
                elif operation == 'crop':
                    crop_params = {
                        'w': params.get('w'),
                        'h': params.get('h'),
                        'x': params.get('x', 0),
                        'y': params.get('y', 0),
                        'g': params.get('g', 'nw'),
                        'p': params.get('p', 100)
                    }
                    current_image_data = crop_image(current_image_data, crop_params)
                    
                elif operation == 'watermark':
                    # Ensure color is properly formatted
                    color = params.get('color', '000000')
                    if color and len(color) < 6:
                        color = color.zfill(6)  # Pad with leading zeros if needed
                        
                    watermark_params = {
                        'text': params.get('text', 'Watermark'),
                        'color': color,
                        't': params.get('t', 100),
                        'g': params.get('g', 'se'),
                        'x': params.get('x', 10),
                        'y': params.get('y', 10),
                        'voffset': params.get('voffset', 0),
                        'fill': params.get('fill', 0),
                        'padx': params.get('padx', 0),
                        'pady': params.get('pady', 0),
                        'size': params.get('size', 40),
                        'shadow': params.get('shadow', 0),
                        'rotate': params.get('rotate', 0)
                    }
                    current_image_data = add_watermark(current_image_data, **watermark_params)
                
                elif operation == 'format':
                    format_params = {
                        'f': params.get('f', 'jpg'),
                        'q': params.get('q', 85)
                    }
                    current_image_data = convert_format(current_image_data, format_params)
                    content_type = get_content_type(format_params['f'])
                
                elif operation == 'quality':
                    quality_params = {}
                    if 'q' in params:
                        quality_params['q'] = params['q']
                    if 'Q' in params:
                        quality_params['Q'] = params['Q']
                    current_image_data = transform_quality(current_image_data, quality_params)
                
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown operation: {operation}"
                    )

        # If no format operation was specified, determine content type from file extension
        if content_type is None:
            _, file_extension = os.path.splitext(image_key)
            content_type = get_content_type(file_extension[1:] if file_extension else 'jpeg')

        # Generate ETag
        etag = hashlib.md5(current_image_data).hexdigest()

        # Set cache control (1 hour)
        cache_control = "public, max-age=3600"

        # Return the processed image with caching headers
        return Response(
            content=current_image_data,
            media_type=content_type,
            headers={
                "Cache-Control": cache_control,
                "ETag": etag
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/favicon.ico", status_code=status.HTTP_204_NO_CONTENT)
async def favicon():
    return Response(content=b"")

# New document conversion endpoints
@app.post("/document/convert", response_model=ConversionResponse)
async def convert_document(request: ConversionRequest):
    """
    Start an asynchronous document conversion task
    """
    try:
        # Create conversion task
        task = document_converter.create_task(
            input_key=request.input_key,
            input_format=request.input_format,
            output_format=request.output_format,
            output_prefix=request.output_prefix,
            image_dpi=request.image_dpi
        )
        
        # Start async processing
        asyncio.create_task(process_document_conversion(task.task_id))
        
        return ConversionResponse(
            task_id=task.task_id,
            status=task.status,
            message="Conversion task created successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/status/{task_id}", response_model=ConversionTask)
async def get_conversion_status(task_id: str):
    """
    Get the status of a document conversion task
    """
    task = document_converter.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    return task

async def process_document_conversion(task_id: str):
    """
    Process a document conversion task
    """
    task = document_converter.get_task(task_id)
    if not task:
        return
        
    try:
        document_converter.update_task_status(task_id, ConversionStatus.PROCESSING)
        
        # Get S3 client and config
        s3_config = S3Config()
        s3_client = get_s3_client()
        
        # Download input document
        input_data = get_document_from_s3(
            s3_client,
            s3_config.bucket_name,
            task.input_key
        )
        
        # Get appropriate format handler
        handler = get_handler(task.input_format)
        
        # Process based on output format
        if task.output_format == OutputFormat.PDF:
            # Convert to PDF
            output_data = handler.convert_to_pdf(input_data, task.image_dpi)
            
            # Upload PDF
            output_key = f"{task.output_prefix}/output.pdf"
            upload_document_to_s3(
                s3_client,
                s3_config.bucket_name,
                output_key,
                output_data,
                get_mime_type('pdf')
            )
            
            # Update task
            document_converter.update_task_status(
                task_id,
                ConversionStatus.COMPLETED,
                output_files=[output_key]
            )
            
        elif task.output_format in {OutputFormat.PNG, OutputFormat.JPEG}:
            # Convert to images
            images = handler.convert_to_images(input_data, task.image_dpi)
            
            # Upload images
            output_files = []
            for filename, image_data in images:
                output_key = f"{task.output_prefix}/{filename}"
                upload_document_to_s3(
                    s3_client,
                    s3_config.bucket_name,
                    output_key,
                    image_data,
                    get_mime_type(task.output_format)
                )
                output_files.append(output_key)
            
            # Update task
            document_converter.update_task_status(
                task_id,
                ConversionStatus.COMPLETED,
                output_files=output_files
            )
            
        elif task.output_format == OutputFormat.TXT:
            if task.input_format not in {
                InputFormat.WORD,
                InputFormat.WORD_X,
                InputFormat.WPS,
                InputFormat.PPT,
                InputFormat.PPT_X
            }:
                raise ValueError(
                    "Only Word and PowerPoint documents can be converted to TXT"
                )
            
            # Convert to text
            text_data = handler.convert_to_text(input_data)
            
            # Upload text file
            output_key = f"{task.output_prefix}/output.txt"
            upload_document_to_s3(
                s3_client,
                s3_config.bucket_name,
                output_key,
                text_data,
                get_mime_type('txt')
            )
            
            # Update task
            document_converter.update_task_status(
                task_id,
                ConversionStatus.COMPLETED,
                output_files=[output_key]
            )
            
    except Exception as e:
        document_converter.update_task_status(
            task_id,
            ConversionStatus.FAILED,
            error_message=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
