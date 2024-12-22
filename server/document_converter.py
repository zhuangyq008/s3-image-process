from enum import Enum
from typing import Optional, List
import os
import uuid
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel

class InputFormat(str, Enum):
    WORD = "doc"
    WORD_X = "docx"
    WPS = "wps"
    EXCEL = "xls"
    EXCEL_X = "xlsx"
    CSV = "csv"
    PPT = "ppt"
    PPT_X = "pptx"
    PDF = "pdf"
    JPEG = "jpeg"

class OutputFormat(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    TXT = "txt"

class ConversionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ConversionTask(BaseModel):
    task_id: str
    input_key: str
    input_format: InputFormat
    output_format: OutputFormat
    output_prefix: str
    status: ConversionStatus
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    output_files: List[str] = []
    image_dpi: Optional[int] = 300
    expires_at: datetime

class DocumentConverter:
    def __init__(self):
        self.tasks = {}
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_tasks())

    async def _cleanup_expired_tasks(self):
        while True:
            now = datetime.now()
            expired_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.expires_at < now
            ]
            for task_id in expired_tasks:
                del self.tasks[task_id]
            await asyncio.sleep(3600)  # Clean up every hour

    def create_task(
        self,
        input_key: str,
        input_format: InputFormat,
        output_format: OutputFormat,
        output_prefix: str,
        image_dpi: Optional[int] = 300
    ) -> ConversionTask:
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = ConversionTask(
            task_id=task_id,
            input_key=input_key,
            input_format=input_format,
            output_format=output_format,
            output_prefix=output_prefix,
            status=ConversionStatus.PENDING,
            created_at=now,
            updated_at=now,
            image_dpi=image_dpi,
            expires_at=now + timedelta(days=7)  # Tasks expire after 7 days
        )
        
        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[ConversionTask]:
        return self.tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: ConversionStatus,
        error_message: Optional[str] = None,
        output_files: Optional[List[str]] = None
    ) -> ConversionTask:
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now()
        
        if error_message is not None:
            task.error_message = error_message
        
        if output_files is not None:
            task.output_files = output_files
        
        return task

    async def process_task(self, task_id: str):
        """
        Process a document conversion task asynchronously.
        This is a placeholder - actual conversion logic will be implemented
        based on input/output formats.
        """
        task = self.get_task(task_id)
        if not task:
            return
        
        try:
            self.update_task_status(task_id, ConversionStatus.PROCESSING)
            
            # TODO: Implement actual conversion logic here
            # This will involve:
            # 1. Downloading from S3
            # 2. Converting format using appropriate library
            # 3. Uploading results back to S3
            # 4. Updating task with output file locations
            
            await asyncio.sleep(1)  # Simulate processing time
            
            # Update task with success status
            self.update_task_status(
                task_id,
                ConversionStatus.COMPLETED,
                output_files=[f"{task.output_prefix}/output.{task.output_format}"]
            )
            
        except Exception as e:
            self.update_task_status(
                task_id,
                ConversionStatus.FAILED,
                error_message=str(e)
            )

# Global converter instance
document_converter = DocumentConverter()
