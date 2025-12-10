import zipfile
import os
from pathlib import Path

def create_zip():
    source = Path("custom_components/ecoflow_api")
    output = Path("ecoflow-api-v1.2.1.zip")
    
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source):
            # Skip __pycache__ and .pyc files
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.pyc') or file == 'hassio-ecoflow-api.code-workspace':
                    continue
                    
                file_path = Path(root) / file
                # Archive path should be ecoflow_api/... (without custom_components/)
                arcname = str(file_path.relative_to("custom_components"))
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")
    
    print(f"\nCreated: {output}")
    print(f"Size: {output.stat().st_size} bytes")

if __name__ == "__main__":
    create_zip()

