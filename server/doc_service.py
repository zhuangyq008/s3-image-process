import logging
from fastapi import FastAPI, Query
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app for document conversion
app = FastAPI(
    title="Document Conversion Service",
    description="Service for converting documents between different formats",
    version="1.0.0"
)

from doc_processor import (
    parse_operation, get_file_extension, process_document, get_task_info
)

@app.post("/doc/{object_key}", tags=["Document Conversion"])
@app.get("/doc/{object_key}", tags=["Document Conversion"])
async def convert_document_handler(
    object_key: str,
    operations: Optional[str] = Query(None, description="Operations to perform, e.g., convert,source_doc,target_png,pages_1,2,4-10")
):
    """
    Convert document with specified operations
    Example: /doc/example.docx?operations=convert,source_doc,target_png,pages_1,2,4-10
    """
    return await process_document(object_key, operations)

@app.get("/doc/task/{task_id}", tags=["Task Status"])
async def get_task_status_handler(task_id: str):
    """Get document conversion task status"""
    return await get_task_info(task_id)

if __name__ == "__main__":
    import uvicorn
    # Run on a different port than the image processing service
    uvicorn.run(app, host="0.0.0.0", port=8001)
