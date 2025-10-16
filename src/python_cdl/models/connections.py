"""CDL connection model for wiring blocks together."""

from pydantic import BaseModel, Field, field_validator


class Connection(BaseModel):
    """Connection between block outputs and inputs."""

    from_block: str = Field(description="Source block name")
    from_output: str = Field(description="Source output connector name")
    to_block: str = Field(description="Target block name")
    to_input: str = Field(description="Target input connector name")
    description: str | None = Field(default=None, description="Natural language description")

    @field_validator("from_block", "to_block")
    @classmethod
    def validate_block_name(cls, v: str) -> str:
        """Validate block name is not empty."""
        if not v or not v.strip():
            raise ValueError("Block name cannot be empty")
        return v.strip()

    @field_validator("from_output", "to_input")
    @classmethod
    def validate_connector_name(cls, v: str) -> str:
        """Validate connector name (can be empty for top-level connections)."""
        # Allow empty string for connections to/from composite block boundary
        if v is None:
            return ""
        return v.strip()

    @property
    def from_path(self) -> str:
        """Get the full path of the source."""
        return f"{self.from_block}.{self.from_output}"

    @property
    def to_path(self) -> str:
        """Get the full path of the target."""
        return f"{self.to_block}.{self.to_input}"

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"
