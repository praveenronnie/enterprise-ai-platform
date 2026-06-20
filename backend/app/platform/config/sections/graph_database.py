# graph_database configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class GraphDatabaseSettings(BaseModel):

    GRAPH_DB_PROVIDER: str = Field(
        description="Graph database provider (e.g. neo4j, neptune).",
    )
    GRAPH_DB_URL: str = Field(
        description="Bolt / HTTPS connection URL.",
    )
    GRAPH_DB_USER: str = Field(
        description="Database username.",
    )
    GRAPH_DB_PASSWORD: str = Field(
        description="Database password.",
    )
    GRAPH_DB_DATABASE: str = Field(
        description="Target database name.",
    )
