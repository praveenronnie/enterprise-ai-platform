from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import aiofiles

from backend.app.agents.ingestion.pipeline import IngestionPipeline
from backend.app.platform.config.storage import StorageManager
from backend.app.platform.dependencies.container import container
from backend.app.shared.models.models import Document

router = APIRouter()


def get_ingestion_pipeline() -> IngestionPipeline:
    pipeline = container.resolve("ingestion_pipeline")
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion pipeline not available.",
        )
    return pipeline


@router.post(
    "/documents/upload",
    summary="Upload and process a PDF document",
    description="Accepts a PDF file via multipart/form-data, processes it with Docling, detects type, extracts via plugin, and performs incremental indexing.",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to process"),
    user_id: str | None = None,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    document_id = str(uuid4())

    upload_dir = StorageManager.document_dir(document_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(file.filename or "document.pdf").name
    file_path = upload_dir / filename

    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    document = Document(
        document_id=document_id,
        filename=filename,
        file_size=len(content),
        file_type=file.content_type,
        checksum="",
        binary_hash="",
    )

    try:
        result = await pipeline.run(
            file_path=file_path, document=document, user_id=user_id
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {exc}",
        )
    finally:
        await file.close()
