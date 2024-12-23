# s3-image-process

This project implements an API for resizing, cropping, watermarking, auto-orienting, and quality transforming images stored in an S3 bucket using FastAPI.

## Project Structure

```
.
├── server/
│   ├── main.py
│   ├── image_processor.py
│   ├── image_cropper.py
│   ├── s3_operations.py
│   ├── watermark.py
│   ├── format_converter.py
│   ├── auto_orient.py
│   ├── quality.py
│   ├── font/
│   │   └── 华文楷体.ttf
│   ├── requirements.txt
│   └── Dockerfile
├── cloudformation.yaml
├── .gitignore
└── README.md
```

## Deployment Instructions

### Local Development Deployment

1. Navigate to the server directory:
   ```
   cd server
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up your AWS credentials:
   - Create a file named `.env` in the `server` directory
   - Add your AWS credentials and S3 bucket information:
     ```
     S3_BUCKET_NAME=your_bucket_name
     ```

6. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

The server will start running on `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.

## API Usage

The API provides a unified endpoint for image processing with operation chaining:

```
/image/{image_key}?operations=operation1,param1_value1/operation2,param1_value1,param2_value2
```

### Example Usage

#### 1. Basic Operations

Test each individual operation:

```
# Auto-orient test
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1

# Resize test (50% of original)
http://127.0.0.1:8000/image/example.jpg?operations=resize,p_50

# Crop test (800x600 from center)
http://127.0.0.1:8000/image/example.jpg?operations=crop,w_800,h_600,g_center

# Watermark test
http://127.0.0.1:8000/image/example.jpg?operations=watermark,text_Q29weXJpZ2h0,g_se,t_80

# Quality test (80% quality)
http://127.0.0.1:8000/image/example.jpg?operations=quality,q_80
```

#### 2. Chained Operations

Complex operations combining multiple transformations:

```
# Chain 1: Auto-orient + Resize + Quality
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/resize,w_800,h_600/quality,q_85

# Chain 2: Resize + Crop + Watermark
http://127.0.0.1:8000/image/example.jpg?operations=resize,p_70/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se

# Chain 3: Auto-orient + Crop + Watermark + Quality
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se/quality,q_85

# Chain 4: Resize + Watermark + Quality
http://127.0.0.1:8000/image/example.jpg?operations=resize,w_1200,h_800/watermark,text_Q29weXJpZ2h0,g_se,t_80/quality,q_90

# Chain 5: All Operations Combined
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/resize,p_70/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se,t_80/quality,q_85
```

## API Parameters

### Operation: auto-orient

- Value: Auto-orientation mode
  - `0`: Keep original orientation (default)
  - `1`: Apply auto-orientation based on EXIF data

Example: `auto-orient,1`

Note: If the original image has no EXIF orientation data, the auto-orient operation will have no effect.

### Operation: resize

- `p`: Percentage for proportional scaling (1-1000)
- `w`: Target width
- `h`: Target height
- `m`: Resize mode
  - `lfit`: Fit within dimensions (default)
  - `mfit`: Minimum fit
  - `fill`: Fill and crop
  - `pad`: Pad with transparency
  - `fixed`: Force exact dimensions

### Operation: crop

- `w`: Crop width
- `h`: Crop height
- `x`: X-axis offset (default: 0)
- `y`: Y-axis offset (default: 0)
- `g`: Gravity point
  - `nw`: Left top
  - `north`: Center top
  - `ne`: Right top
  - `west`: Left center
  - `center`: Center
  - `east`: Right center
  - `sw`: Left bottom
  - `south`: Center bottom
  - `se`: Right bottom
- `p`: Scale percentage after cropping (1-200, default: 100)

### Operation: watermark

- `text`: Base64 encoded watermark text (supports UTF-8, including Chinese)
  - Example: "Hello World" should be encoded as "SGVsbG8gV29ybGQ"
  - Chinese text "版权所有" should be encoded as "54mI5p2D5omA5pyJ"
- `t`: Transparency (0-100, default: 100)
- `g`: Position (nw, north, ne, west, center, east, sw, south, se; default: se)
- `x`: Horizontal offset (0-4096, default: 10)
- `y`: Vertical offset (0-4096, default: 10)
- `voffset`: Vertical offset for center alignments (-1000 to 1000, default: 0)
- `fill`: Fill image with watermark (0 or 1, default: 0)
- `padx`: Horizontal padding between watermarks (0-4096, default: 0)
- `pady`: Vertical padding between watermarks (0-4096, default: 0)
- `size`: Font size (optional, auto-calculated if not specified)

### Operation: quality

- Parameters:
  - `q`: Relative quality (1-100)
    - Compresses the image by the specified percentage
    - Suitable for JPG format relative quality adjustment
    - For WebP format, behaves the same as absolute quality
  - `Q`: Absolute quality (1-100)
    - Sets a fixed quality value
    - Only supports JPG and WebP formats
    - When original quality is higher than target, compresses to target quality
    - When original quality is lower than target, maintains original quality

Note: You must specify either relative (q) or absolute (Q) quality, but not both.

Example usage:
```bash
# Apply relative quality compression (80%)
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=quality,q_80" --output result.jpg

# Set absolute quality value (90)
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=quality,Q_90" --output result.jpg

# Chain with other operations
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=resize,w_800/quality,q_85" --output result.jpg
```

### Watermark Features

1. Chinese Text Support:
   - Built-in support for Chinese characters using 华文楷体.ttf
   - Clear and readable text rendering
   - Automatic font size scaling based on image dimensions
   - Base64 encoded text input for proper character handling

2. Enhanced Visibility:
   - Semi-transparent background for better contrast
   - Optimized text opacity
   - Increased padding around text
   - Default size of 1/20 of image's smaller dimension

3. Best Practices:
   - Always encode watermark text in base64 format
   - Use default transparency (t=100) for maximum clarity
   - Position away from busy image areas (g=se is default)
   - For small images or when text is unclear, specify a larger size parameter
   - Use concise text for better readability

## Caching

The API implements caching headers to improve performance:

- `Cache-Control: public, max-age=3600`: Allows caching of the processed image for 1 hour.
- `ETag`: Provides a unique identifier for each processed image, enabling efficient cache validation.

## Cleanup

To remove all resources created by this stack, delete the stack from the CloudFormation console or using the AWS CLI.

## Note

This README assumes you're running the server locally. For production deployment, replace `http://127.0.0.1:8000` with your actual API endpoint URL.
