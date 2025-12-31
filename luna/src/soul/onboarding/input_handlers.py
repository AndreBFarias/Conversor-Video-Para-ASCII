from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.soul.onboarding.core import OnboardingProcess

logger = logging.getLogger(__name__)


async def wait_for_text_input(process: OnboardingProcess, timeout=None):
    loop = asyncio.get_event_loop()
    process.input_future = loop.create_future()
    try:
        if timeout:
            return await asyncio.wait_for(process.input_future, timeout)
        else:
            return await process.input_future
    except asyncio.TimeoutError:
        return ""
    except asyncio.CancelledError:
        return ""


async def wait_for_button_click(process: OnboardingProcess, button_id: str, timeout=None):
    loop = asyncio.get_event_loop()
    process.button_future = loop.create_future()
    process.waiting_for_button = button_id

    try:
        if timeout:
            return await asyncio.wait_for(process.button_future, timeout)
        else:
            return await process.button_future
    except asyncio.TimeoutError:
        process.waiting_for_button = None
        return False
    except asyncio.CancelledError:
        return False


def handle_text_input(process: OnboardingProcess, text: str) -> bool:
    if process.input_future and not process.input_future.done():
        loop = process.input_future.get_loop()
        loop.call_soon_threadsafe(process.input_future.set_result, text)
        return True
    return False


def handle_button_click(process: OnboardingProcess, button_id: str) -> bool:
    if process.waiting_for_button == button_id:
        if process.button_future and not process.button_future.done():
            loop = process.button_future.get_loop()
            loop.call_soon_threadsafe(process.button_future.set_result, True)
            process.waiting_for_button = None
            return True
    return False


def extract_name(text: str) -> str:
    text = text.strip()
    triggers = ["meu nome é", "eu sou", "chame de", "me chamo", "pode me chamar de"]
    lower = text.lower()

    for t in triggers:
        if t in lower:
            parts = lower.split(t)
            if len(parts) > 1:
                start_index = lower.find(t) + len(t)
                raw_name = text[start_index:].strip()
                raw_name = re.sub(r'[.,!?;:\'"]+', "", raw_name)
                return raw_name.split()[0].title() if raw_name.split() else raw_name.title()

    clean_text = re.sub(r'[.,!?;:\'"]+', "", text)
    if len(clean_text.split()) <= 2:
        return clean_text.split()[0].title() if clean_text.split() else clean_text.title()
    return clean_text.split()[0].title()
