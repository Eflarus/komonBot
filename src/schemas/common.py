from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None


class ImageUploadResponse(BaseModel):
    url: str
