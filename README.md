# s3-image-process

This project implements an API for resizing images stored in an S3 bucket using AWS Lambda and API Gateway.

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
└── README.md
```

## Deployment Instructions

### Local Deployment

```
cd server
uvicorn main:app --reload
```

### 1. Prepare the Docker Image

1. Build the Docker image:

   ```
   cd server
   docker build -t s3-image-resize .
   ```
2. Tag the image:

   ```
   docker tag s3-image-resize:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/image-resize-repo:latest
   ```
3. Push the image to ECR:

   ```
   aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

   docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/image-resize-repo:latest
   ```

### 2. Deploy the CloudFormation Stack

1. Open the AWS CloudFormation console.
2. Click "Create stack" and choose "With new resources (standard)".
3. Upload the `cloudformation.yaml` file.
4. Fill in the stack details:
   - Stack name: Choose a name for your stack
   - Parameters:
     - ImageBucket: Name of your S3 bucket for storing images
     - ImageBucketPrefix: Prefix for image storage in the S3 bucket (can be left empty)
     - ECRImageUri: URI of your ECR image (e.g., `<your-account-id>.dkr.ecr.<your-region>.amazonaws.com/image-resize-repo:latest`)
5. Review and create the stack.

After the stack is created, you can find the API endpoint URL in the Outputs tab of the CloudFormation stack.

## API Usage

The API supports various image resizing options. Here are some use cases and example curl commands:

### 1. Resize an image proportionally to 50% of its original size

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "p": 50
  }'
```

### 2. Resize an image to a specific width (800px) while maintaining aspect ratio

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "w": 800,
    "m": "lfit"
  }'
```

### 3. Resize an image to fit within a 800x600 box, maintaining aspect ratio

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "w": 800,
    "h": 600,
    "m": "lfit"
  }'
```

### 4. Resize an image to cover a 800x600 area and crop the excess

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "w": 800,
    "h": 600,
    "m": "fill"
  }'
```

### 5. Resize an image to fit within a 800x600 box and pad with transparency

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "w": 800,
    "h": 600,
    "m": "pad"
  }'
```

### 6. Force resize an image to exactly 800x600, ignoring aspect ratio

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "w": 800,
    "h": 600,
    "m": "fixed"
  }'
```

### 7. Resize an image to 150% of its original size

```bash
curl -X POST https://<your-api-id>.execute-api.<your-region>.amazonaws.com/prod/resize \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "example.jpg",
    "p": 150
  }'
```

## API Parameters

- `image_key`: The key of the image in the S3 bucket
- `p`: Percentage for proportional scaling (1-1000)
- `w`: Target width
- `h`: Target height
- `m`: Resize mode (lfit, mfit, fill, pad, fixed)

## Cleanup

To remove all resources created by this stack, delete the stack from the CloudFormation console or using the AWS CLI.
