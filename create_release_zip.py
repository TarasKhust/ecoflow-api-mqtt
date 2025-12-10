#!/usr/bin/env python3
"""Create release zip archive for EcoFlow API integration."""
import shutil
import os
from pathlib import Path

def create_release_zip(version: str):
    """Create a zip archive for the release."""
    base_dir = Path(__file__).parent
    source_dir = base_dir / "custom_components" / "ecoflow_api"
    output_file = base_dir / f"ecoflow-api-v{version}.zip"
    
    # Remove old zip if exists
    if output_file.exists():
        output_file.unlink()
        print(f"Removed old archive: {output_file}")
    
    # Create zip archive
    print(f"Creating archive from: {source_dir}")
    print(f"Output file: {output_file}")
    
    # Create temporary directory structure
    temp_dir = base_dir / "temp_release"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    temp_ecoflow = temp_dir / "ecoflow_api"
    temp_ecoflow.mkdir(parents=True)
    
    # Copy files
    for item in source_dir.iterdir():
        if item.name == "__pycache__":
            continue
        if item.name.endswith(".pyc"):
            continue
        if item.name == "hassio-ecoflow-api.code-workspace":
            continue
            
        if item.is_file():
            shutil.copy2(item, temp_ecoflow / item.name)
            print(f"  Copied: {item.name}")
        elif item.is_dir():
            shutil.copytree(item, temp_ecoflow / item.name, 
                          ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print(f"  Copied dir: {item.name}")
    
    # Create zip
    shutil.make_archive(str(output_file.with_suffix("")), "zip", temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"\n✅ Archive created successfully!")
        print(f"   File: {output_file.name}")
        print(f"   Size: {size:,} bytes")
        return True
    else:
        print(f"\n❌ Failed to create archive!")
        return False

if __name__ == "__main__":
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else "1.1.4"
    success = create_release_zip(version)
    sys.exit(0 if success else 1)

