"""Semantic metadata models for CDL blocks and connectors."""

from typing import Any

from pydantic import BaseModel, Field


class SemanticMetadata(BaseModel):
    """Semantic metadata using standard ontologies."""

    metadata_language: str | None = Field(
        default=None,
        description="Metadata language (e.g., 'Brick', 'Haystack', 'S223p')",
    )
    natural_language: str | None = Field(
        default=None,
        description="Natural language description",
    )
    brick_annotation: dict[str, Any] | None = Field(
        default=None,
        description="Brick schema annotations",
    )
    haystack_annotation: dict[str, Any] | None = Field(
        default=None,
        description="Project Haystack annotations",
    )
    s223p_annotation: dict[str, Any] | None = Field(
        default=None,
        description="ASHRAE S223p annotations",
    )
    custom_annotations: dict[str, Any] | None = Field(
        default=None,
        description="Custom vendor-specific annotations",
    )

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "allow"
