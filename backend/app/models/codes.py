from pydantic import BaseModel


class CodeResult(BaseModel):
    code: str
    description: str
    category: str


class CodeSearchResponse(BaseModel):
    results: list[CodeResult]
