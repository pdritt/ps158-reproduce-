"""Download original Federal Reserve SCF summary extracts (2025-dollar vintage)."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
YEARS = range(1989, 2026, 3)
BASE = 'https://www.federalreserve.gov/econres/files/'

def download(url, target):
    temporary = target.with_suffix(target.suffix + '.part')
    subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                    '--retry', '3', '--max-time', '120', url, '-o', str(temporary)], check=True)
    temporary.replace(target)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Download again even if cached.')
    args = parser.parse_args()
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    manifest = []
    for year in YEARS:
        name = f'scfp{year}excel.zip'
        target = data / name
        if args.refresh or not target.exists():
            download(BASE + name, target)
        with zipfile.ZipFile(target) as archive:
            members = [n for n in archive.namelist() if n.lower().endswith('.csv')]
            if len(members) != 1:
                raise ValueError(f'Expected one CSV in {name}: {members}')
            # Write to a fixed safe filename rather than extracting archive paths.
            (data / f'scf{year}.csv').write_bytes(archive.read(members[0]))
        manifest.append({'year': year, 'url': BASE + name,
                         'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        print(f'{year}: downloaded/validated original SCF extract', flush=True)
    download(BASE + 'bulletin.macro.txt', data / 'bulletin.macro.txt')
    (data / 'sources.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == '__main__':
    main()
