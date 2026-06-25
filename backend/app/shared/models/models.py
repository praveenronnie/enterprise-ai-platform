"""Core domain models used throughout the Enterprise AI Platform."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from enum import Enum


def _current_time() -> datetime:
    return datetime.now()


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Image(BaseModel):
    document_id: str
    image_id: str
    page_number: int
    image_index: int
    caption: str
    width: float
    height: float
    bounding_box: tuple[float, float, float, float]
    file_path: str
    mime_type: str
    description: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class Table(BaseModel):
    document_id: str
    table_id: str
    page_number: int
    table_index: int
    markdown: str
    html: str
    csv: str
    bounding_box: tuple[float, float, float, float]
    description: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    page_numbers: list[int] = Field(default_factory=list)
    section_title: str | None = None
    heading_level: int | None = None
    text: str
    content_hash: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class Document(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    checksum: str
    source: str | None = None
    binary_hash: str
    doc_version: int = 1

    title: str | None = None
    main_topic: str | None = None
    summary: str | None = None
    author: str | None = None
    language: str | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None
    headings: list[str] = Field(default_factory=list)

    total_pages: int = 0
    total_words: int = 0

    has_images: bool = False
    has_tables: bool = False
    has_charts: bool = False
    has_equations: bool = False
    has_code_blocks: bool = False
    has_handwriting: bool = False
    do_ocr: bool = False
    ocr_status: ProcessingStatus = ProcessingStatus.PENDING
    ocr_confidence: int = 0

    chunked: bool = False
    embedded: bool = False
    entities_extracted: bool = False
    graph_created: bool = False
    indexed: bool = False
    evaluated: bool = False
    chunk_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)

    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)

    metadata_confidence: float | None = None
    topic_confidence: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_current_time)
    updated_at: datetime = Field(default_factory=_current_time)

    extracted_text: str = ""
    pages: list[dict[str, str | int]] = Field(default_factory=list)
    images: list[Image] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    processing_metadata: dict[str, str] = Field(default_factory=dict)


class Entity(BaseModel):
    entity_id: str
    document_id: str
    chunk_id: str
    name: str
    label: str
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)
    confidence: float | None = None


class Relation(BaseModel):
    relation_id: str
    document_id: str
    source_entity_id: str
    target_entity_id: str
    relation: str
    description: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)
    confidence: float | None = None


class Graph(BaseModel):
    graph_id: str
    document_id: str
    entity_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_current_time)