import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("secure_gateway.audit")


def audit(
    *,
    request_id: str,
    principal_id: str,
    role: str | None,
    tool_name: str,
    decision: str,
    reason_code: str,
    query: str | None = None,
    policy_id: int | None = None,
) -> None:
    event: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "principal_id": principal_id,
        "role": role,
        "tool_name": tool_name,
        "decision": decision,
        "reason_code": reason_code,
    }
    if query is not None:
        event["query_hash"] = hashlib.sha256(query.encode("utf-8")).hexdigest()
    if policy_id is not None:
        event["policy_version"] = policy_id
    logger.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
