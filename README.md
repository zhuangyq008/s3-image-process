# s3-image-process

This project implements an API for resizing images stored in an S3 bucket using FastAPI.

## Project Structure

```
.
├── server/
│   ├── main.py
│   ├── image_processor.py
│   ├── s3_operations.py
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

The API now returns the resized image directly, instead of an S3 key. Here are some use cases and example curl commands:

### 1. Resize an image proportionally to 50% of its original size

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?p=50" --output resized_image.jpg
```

### 2. Resize an image to a specific width (800px) while maintaining aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&m=lfit" --output resized_image.jpg
```

### 3. Resize an image to fit within a 800x600 box, maintaining aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=lfit" --output resized_image.jpg
```

### 4. Resize an image to cover a 800x600 area and crop the excess

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=fill" --output resized_image.jpg
```

### 5. Resize an image to fit within a 800x600 box and pad with transparency

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=pad" --output resized_image.jpg
```

### 6. Force resize an image to exactly 800x600, ignoring aspect ratio

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?w=800&h=600&m=fixed" --output resized_image.jpg
```

### 7. Resize an image to 150% of its original size

```bash
curl -X GET "http://127.0.0.1:8000/resize/example.jpg?p=150" --output resized_image.jpg
```

## API Parameters

- `image_key`: The key of the image in the S3 bucket (specified as a path variable)
- `p`: Percentage for proportional scaling (1-1000)
- `w`: Target width
- `h`: Target height
- `m`: Resize mode (lfit, mfit, fill, pad, fixed)

## Caching

The API implements caching headers to improve performance:

- `Cache-Control: public, max-age=3600`: Allows caching of the resized image for 1 hour.
- `ETag`: Provides a unique identifier for each resized image, enabling efficient cache validation.

## Cleanup

To remove all resources created by this stack, delete the stack from the CloudFormation console or using the AWS CLI.

## Note

This README assumes you're running the server locally. For production deployment, replace `http://127.0.0.1:8000` with your actual API endpoint URL.
