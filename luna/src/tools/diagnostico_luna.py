#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.diagnostico_luna import LunaDiagnostico, TestResult, main

__all__ = [
    "TestResult",
    "LunaDiagnostico",
    "main",
]

if __name__ == "__main__":
    main()
