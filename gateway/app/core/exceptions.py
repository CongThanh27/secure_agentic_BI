class GatewayError(Exception):
    """Base class for expected security and upstream errors."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class PolicyError(GatewayError):
    """The policy source is unavailable or the principal has no policy."""
