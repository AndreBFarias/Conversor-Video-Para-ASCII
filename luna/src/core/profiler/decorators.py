from __future__ import annotations

import asyncio
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import LunaProfiler


def profile(stage: str = None):
    def decorator(func):
        nonlocal stage
        if stage is None:
            stage = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            from .core import get_profiler

            profiler = get_profiler()
            with profiler.span(stage):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            from .core import get_profiler

            profiler = get_profiler()
            with profiler.span(stage):
                return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
