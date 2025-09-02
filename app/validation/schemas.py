from pydantic import BaseModel
from typing import Dict, Any

class ValidationResult(BaseModel):
    success: bool
    statistics: Dict[str, Any]
    meta: Dict[str, Any]
    results: Dict[str, Any]

class ValidationErrorDetail(BaseModel):
    expectation_config: Dict[str, Any]
    result: Dict[str, Any]
    exception_info: Dict[str, Any]
