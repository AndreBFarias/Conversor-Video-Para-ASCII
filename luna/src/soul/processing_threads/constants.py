import re

RE_CODE_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

_SENSITIVE_RE = re.compile(
    r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)|"
    r"(\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b)|"
    r"(\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}\b)",
    re.IGNORECASE,
)

RE_ACTION = re.compile(r"\[([^\]]*(?:Luna|luna)[^\]]*)\]")
