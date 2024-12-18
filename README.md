# s3-image-process

This project implements an API for resizing, cropping, and watermarking images stored in an S3 bucket using FastAPI.

## Project Structure

```
.
├── server/
│   ├── main.py
│   ├── image_processor.py
│   ├── image_cropper.py
│   ├── s3_operations.py
│   ├── watermark.py
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

### Production Deployment

[Keep the existing Docker and CloudFormation instructions]

## API Usage

The API now returns the processed image directly, instead of an S3 key. Here are some use cases and example curl commands:

### Resize API

#### 1. Resize an image proportionally to 50% of its original size

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?p=50" --output resized_image.jpg
```

#### 2. Resize an image to a specific width (800px) while maintaining aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&m=lfit" --output resized_image.jpg
```

#### 3. Resize an image to fit within a 800x600 box, maintaining aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=lfit" --output resized_image.jpg
```

#### 4. Resize an image to cover a 800x600 area and crop the excess

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=fill" --output resized_image.jpg
```

#### 5. Resize an image to fit within a 800x600 box and pad with transparency

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=pad" --output resized_image.jpg
```

#### 6. Force resize an image to exactly 800x600, ignoring aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=fixed" --output resized_image.jpg
```

#### 7. Resize an image to 150% of its original size

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?p=150" --output resized_image.jpg
```

### Crop API

#### 1. Crop an image to 800x600 from the center

```bash
curl -X GET "http://127.0.0.1:8000/crop/example.jpg?w=800&h=600&g=center" --output cropped_image.jpg
```

#### 2. Crop an image from the top-left corner with offset

```bash
curl -X GET "http://127.0.0.1:8000/crop/example.jpg?w=800&h=600&g=nw&x=100&y=50" --output cropped_image.jpg
```

#### 3. Crop and scale the result to 150%

```bash
curl -X GET "http://127.0.0.1:8000/crop/example.jpg?w=800&h=600&g=center&p=150" --output cropped_image.jpg
```

#### 4. Crop from the bottom-right corner

```bash
curl -X GET "http://127.0.0.1:8000/crop/example.jpg?w=800&h=600&g=se" --output cropped_image.jpg
```

### Watermark API

#### Add a watermark to an image

```bash
curl -X GET "http://127.0.0.1:8000/watermark/example.jpg?text=Copyright&t=50&g=se&x=20&y=20" --output watermarked_image.jpg
```

## API Parameters

### Resize API Parameters

- `image_key`: The key of the image in the S3 bucket (specified as a path variable)
- `p`: Percentage for proportional scaling (1-1000)
- `w`: Target width
- `h`: Target height
- `m`: Resize mode (lfit, mfit, fill, pad, fixed)

### Crop API Parameters

- `image_key`: The key of the image in the S3 bucket (specified as a path variable)
- `w`: Crop width (optional)
- `h`: Crop height (optional)
- `x`: X-axis offset (default: 0)
- `y`: Y-axis offset (default: 0)
- `g`: Gravity point for cropping (default: nw)
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

### Watermark API Parameters

- `image_key`: The key of the image in the S3 bucket (specified as a path variable)
- `text`: Watermark text (required)
- `t`: Transparency of the watermark (0-100, default: 100)
- `g`: Position of the watermark (nw, north, ne, west, center, east, sw, south, se; default: se)
- `x`: Horizontal offset (0-4096, default: 10)
- `y`: Vertical offset (0-4096, default: 10)
- `voffset`: Vertical offset for center alignments (-1000 to 1000, default: 0)
- `fill`: Fill the image with watermark (0 or 1, default: 0)
- `padx`: Horizontal padding between watermarks (0-4096, default: 0)
- `pady`: Vertical padding between watermarks (0-4096, default: 0)

## Caching

The API implements caching headers to improve performance:

- `Cache-Control: public, max-age=3600`: Allows caching of the processed image for 1 hour.
- `ETag`: Provides a unique identifier for each processed image, enabling efficient cache validation.

## Cleanup

To remove all resources created by this stack, delete the stack from the CloudFormation console or using the AWS CLI.

## Note

This README assumes you're running the server locally. For production deployment, replace `http://127.0.0.1:8000` with your actual API endpoint URL.
