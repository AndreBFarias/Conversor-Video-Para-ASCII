# -*- coding: utf-8 -*-
import importlib
import sys
from typing import Any, Optional
from functools import lru_cache


class LazyModule:
    def __init__(self, module_name: str, package: Optional[str] = None):
        self._module_name = module_name
        self._package = package
        self._module = None

    def _load(self):
        if self._module is None:
            try:
                self._module = importlib.import_module(self._module_name, self._package)
            except ImportError as e:
                raise ImportError(f"Modulo '{self._module_name}' nao disponivel: {e}")
        return self._module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __repr__(self) -> str:
        if self._module is None:
            return f"<LazyModule '{self._module_name}' (not loaded)>"
        return f"<LazyModule '{self._module_name}' (loaded)>"


class LazyImporter:
    _instances = {}

    @classmethod
    def get(cls, module_name: str) -> LazyModule:
        if module_name not in cls._instances:
            cls._instances[module_name] = LazyModule(module_name)
        return cls._instances[module_name]

    @classmethod
    def is_loaded(cls, module_name: str) -> bool:
        if module_name not in cls._instances:
            return False
        return cls._instances[module_name]._module is not None

    @classmethod
    def preload(cls, *module_names: str) -> None:
        for name in module_names:
            try:
                cls.get(name)._load()
            except ImportError:
                pass


@lru_cache(maxsize=1)
def get_cupy():
    try:
        import cupy as cp
        cp.cuda.Device(0).compute_capability
        return cp
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_mediapipe():
    try:
        import mediapipe as mp
        return mp
    except ImportError:
        return None


@lru_cache(maxsize=1)
def get_cv2_cuda():
    try:
        import cv2
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            return cv2.cuda
        return None
    except Exception:
        return None


def is_gpu_available() -> bool:
    return get_cupy() is not None


def is_mediapipe_available() -> bool:
    return get_mediapipe() is not None


def is_cv2_cuda_available() -> bool:
    return get_cv2_cuda() is not None


# "O homem que le demais e pensa de menos contrai habitos de preguica mental." - Albert Einstein
