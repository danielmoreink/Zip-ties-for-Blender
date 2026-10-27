from pathlib import Path
import zipfile
import tomllib
import re

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root/'node_zip_ties'/'blender_manifest.toml').read_text())['version']

# Keep the repository and bundled user guides aligned with every new package.
download = f'https://github.com/danielmoreink/Zip-ties-for-Blender/raw/refs/heads/master/dist/node_zip_ties-{version}.zip'
release_block = f'<!-- current-release:start -->\n**[Download current release — v{version}]({download})**\n<!-- current-release:end -->'
for readme in [root/'README.md',root/'node_zip_ties'/'README.md']:
    original = readme.read_text(encoding='utf8')
    updated,count = re.subn(r'<!-- current-release:start -->.*?<!-- current-release:end -->',
                           lambda _: release_block,original,count=1,flags=re.DOTALL)
    if not count:
        heading,body = original.split('\n',1)
        updated = heading+'\n\n'+release_block+'\n'+body
    if updated != original:
        readme.write_text(updated,encoding='utf8')
destination = root / 'dist' / f'node_zip_ties-{version}.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted((root/'node_zip_ties').rglob('*')):
        if file.is_file() and '__pycache__' not in file.parts:
            archive.write(file,file.relative_to(root/'node_zip_ties'))
print(destination)
