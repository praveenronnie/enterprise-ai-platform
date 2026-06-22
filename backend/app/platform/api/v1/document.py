from pathlib import Path
from uuid import uuid4
from pprint import pprint

from fastapi import APIRouter, File, HTTPException, UploadFile, status
import aiofiles

from backend.app.platform.config.storage import StorageManager
from backend.app.shared.models.models import Document
from backend.app.shared.services.document_processor import process_document

router = APIRouter()


@router.post(
    "/documents/upload",
    response_model=Document,
    summary="Upload and process a PDF document",
    description="Accepts a PDF file via multipart/form-data, processes it with Docling, and returns the extracted document data.",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to process"),
) -> Document:
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

    # try:
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

    result = process_document(
        file_path=file_path,
        document=document,
    )

    pprint(result.model_dump())
    return result

    """except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {exc}",
        )
    finally:
        await file.close()"""
