import os
import hashlib
from fastapi import FastAPI, Query, status, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from PIL import Image
import io

from image_resizer import resize_image, ResizeMode
from image_cropper import crop_image, CropGravity
from s3_operations import S3Config, get_s3_client, download_image_from_s3
from watermark import add_watermark
from format_converter import convert_format, ImageFormat
from auto_orient import auto_orient_image
from quality import transform_quality

# Configuration class
class ImageProcessingConfig(BaseModel):
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_formats: list = ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"]

# FastAPI app
app = FastAPI()

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

@app.get("/watermark/{image_key}")
async def watermark_image_endpoint(
    image_key: str,
    text: str = Query(..., description="Watermark text"),
    color: str = Query("000000", description="Text color in hex format (e.g., FF0000 for red)"),
    t: int = Query(100, ge=0, le=100, description="Transparency of the watermark"),
    g: str = Query("se", description="Position of the watermark"),
    x: int = Query(10, ge=0, le=4096, description="Horizontal offset"),
    y: int = Query(10, ge=0, le=4096, description="Vertical offset"),
    voffset: int = Query(0, ge=-1000, le=1000, description="Vertical offset for center alignments"),
    fill: int = Query(0, ge=0, le=1, description="Fill the image with watermark"),
    padx: int = Query(0, ge=0, le=4096, description="Horizontal padding between watermarks"),
    pady: int = Query(0, ge=0, le=4096, description="Vertical padding between watermarks"),
    size: int = Query(40, gt=0, le=1000, description="Font size"),
    shadow: int = Query(0, ge=0, le=100, description="Shadow transparency"),
    rotate: int = Query(0, ge=0, le=360, description="Rotation angle")
):
    params = [f"text_{text}"]
    if color != "000000":
        params.append(f"color_{color}")
    if t != 100:
        params.append(f"t_{t}")
    if g != "se":
        params.append(f"g_{g}")
    if x != 10:
        params.append(f"x_{x}")
    if y != 10:
        params.append(f"y_{y}")
    if voffset != 0:
        params.append(f"voffset_{voffset}")
    if fill != 0:
        params.append(f"fill_{fill}")
    if padx != 0:
        params.append(f"padx_{padx}")
    if pady != 0:
        params.append(f"pady_{pady}")
    if size != 40:
        params.append(f"size_{size}")
    if shadow != 0:
        params.append(f"shadow_{shadow}")
    if rotate != 0:
        params.append(f"rotate_{rotate}")
    
    operations = f"watermark,{','.join(params)}"
    return await process_image(image_key, operations)

@app.get("/crop/{image_key}")
async def crop_image_endpoint(
    image_key: str,
    w: Optional[int] = Query(None, gt=0, description="Crop width"),
    h: Optional[int] = Query(None, gt=0, description="Crop height"),
    x: int = Query(0, ge=0, description="X-axis offset"),
    y: int = Query(0, ge=0, description="Y-axis offset"),
    g: CropGravity = Query(CropGravity.NW, description="Gravity point for cropping"),
    p: int = Query(100, ge=1, le=200, description="Scale percentage after cropping")
):
    params = []
    if w is not None:
        params.append(f"w_{w}")
    if h is not None:
        params.append(f"h_{h}")
    if x != 0:
        params.append(f"x_{x}")
    if y != 0:
        params.append(f"y_{y}")
    if g != CropGravity.NW:
        params.append(f"g_{g}")
    if p != 100:
        params.append(f"p_{p}")
    
    operations = f"crop,{','.join(params)}"
    return await process_image(image_key, operations)

@app.get("/quality/{image_key}")
async def quality_image_endpoint(
    image_key: str,
    q: Optional[int] = Query(None, ge=1, le=100, description="Relative quality (1-100)"),
    Q: Optional[int] = Query(None, ge=1, le=100, description="Absolute quality (1-100)")
):
    """Transform image quality using relative or absolute quality parameters"""
    if q is not None and Q is not None:
        raise HTTPException(status_code=400, detail="Cannot specify both relative and absolute quality")
    if q is None and Q is None:
        raise HTTPException(status_code=400, detail="Must specify either relative (q) or absolute (Q) quality")
    
    params = []
    if q is not None:
        params.append(f"q_{q}")
    if Q is not None:
        params.append(f"Q_{Q}")
    
    operations = f"quality,{','.join(params)}"
    return await process_image(image_key, operations)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
