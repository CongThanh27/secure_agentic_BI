from typing import Annotated, Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: Annotated[str, Field(min_length=1)]
    role: Annotated[str, Field(min_length=1)]


class ReflexionChatRequest(ChatRequest):
    max_iterations: Annotated[int, Field(ge=1, le=10)] = 3


class PermissionsResponse(BaseModel):
    role_name: str
    allowed_catalogs: list[str]
    allowed_tables: list[str]
    denied_tables: list[str]
    can_export_file: bool
    max_row_limit: int
    can_execute_ddl: bool
    can_access_pii: bool
    created_at: str
    updated_by: str


class ChatResponse(BaseModel):
    query: str
    role_name: str
    filtered_schema: str
    agent_plan: dict[str, Any]
    status: str
    reason: str
    sql: str


class ReflexionIteration(BaseModel):
    attempt_number: int
    generated_sql: str
    error_message: str
    status: str


class ReflexionChatResponse(BaseModel):
    query: str
    role: str
    status: str
    total_iterations_used: int
    iteration_history: list[ReflexionIteration]
    final_data: Any | None = None


class SecurePipelineRequest(ReflexionChatRequest):
    timeout_seconds: Annotated[float, Field(gt=0, le=120)] = 5.0


class SecurePipelineResponse(BaseModel):
    status: str
    total_iterations_used: int
    execution_time_seconds: float
    iteration_history: list[ReflexionIteration]
    raw_data: Any | None = None
    final_answer: str
