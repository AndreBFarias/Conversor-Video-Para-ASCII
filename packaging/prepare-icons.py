#!/usr/bin/env python3

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def resize_icon(source: Path, output: Path, size: tuple[int, int]):
    img = Image.open(source)
    img = img.resize(size, Image.Resampling.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG")
    print(f"Created {output.name} ({size[0]}x{size[1]})")

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    assets_dir = project_root / "assets"

    source_icon = assets_dir / "logo.png"

    if not source_icon.exists():
        print(f"Error: {source_icon} not found")
        sys.exit(1)

    sizes = {
        "logo-64.png": (64, 64),
        "logo-128.png": (128, 128),
        "logo-512.png": (512, 512),
    }

    for filename, size in sizes.items():
        output_path = assets_dir / filename
        resize_icon(source_icon, output_path, size)

    print("\nIcons prepared successfully")

if __name__ == "__main__":
    main()
