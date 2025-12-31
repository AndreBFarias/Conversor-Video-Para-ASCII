"""
Visao - Sistema de visao computacional

Este modulo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/visao/
"""

from src.soul.visao import (
    IMAGEHASH_AVAILABLE,
    CameraManager,
    ChangeDetector,
    FaceAnalyzer,
    GeminiVisionProvider,
    ImageAnalyzer,
    OllamaVisionProvider,
    PersonProfileManager,
    VisionCache,
    VisionProviderFactory,
    Visao,
    frame_to_base64,
)

__all__ = [
    "Visao",
    "CameraManager",
    "ImageAnalyzer",
    "FaceAnalyzer",
    "ChangeDetector",
    "IMAGEHASH_AVAILABLE",
    "VisionCache",
    "PersonProfileManager",
    "GeminiVisionProvider",
    "OllamaVisionProvider",
    "VisionProviderFactory",
    "frame_to_base64",
]
