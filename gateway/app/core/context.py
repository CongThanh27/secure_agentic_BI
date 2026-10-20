from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    principal_id: str
    role: str

    @classmethod
    def create(cls, principal_id: str, role: str) -> "RequestContext":
        return cls(request_id=str(uuid4()), principal_id=principal_id, role=role)
