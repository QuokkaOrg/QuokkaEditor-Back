from pydantic import BaseModel, Field


class ProjectUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=250)
