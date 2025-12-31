from .constants import _SENSITIVE_RE


def sanitize_log(text: str, max_len: int = 50) -> str:
    if not text:
        return ""
    sanitized = _SENSITIVE_RE.sub("[REDACTED]", text)
    return f"{sanitized[:max_len]}..." if len(sanitized) > max_len else sanitized
