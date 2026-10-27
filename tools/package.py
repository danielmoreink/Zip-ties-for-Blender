from pathlib import Path
import zipfile
import tomllib

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root/'node_zip_ties'/'blender_manifest.toml').read_text())['version']
destination = root / 'dist' / f'node_zip_ties-{version}.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted((root/'node_zip_ties').rglob('*')):
        if file.is_file() and '__pycache__' not in file.parts:
            archive.write(file,file.relative_to(root/'node_zip_ties'))
print(destination)
