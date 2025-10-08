# carcols-normalizer

[![CI](https://img.shields.io/github/actions/workflow/status/cal1ber/carcols-normalizer/ci.yml?label=CI)](../../actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)]()

Normalize `carcols.meta` **VMT_EGNINE | VMT_GEARBOX | VMT_BRAKES * item runs** across subfolders:
- Finds `carcols.meta` files recursively
- Detects consecutive `<Item>…</Item>` blocks by `<type>` (e.g., `VMT_GEARBOX`)
- Replaces each run with exactly **four** `<Item>` entries with `modifier` values **25, 50, 75, 100**
- Creates a `.bak` backup before any change
- Bonus: clean up backups interactively

> Not affiliated with Rockstar Games. Use at your own risk.

## Features
- Robust: parses items, not a fragile single regex
- Indentation preserved
- Works on Windows paths (including `[]` folders)

## Install
No deps; standard library only. Requires **Python 3.8+**.

## Usage

## Script Options
```sql
positional arguments:
  root                     root folder to scan (default points to your example)

options:
  --any                    operate on ANY VMT_* type
  -n, --dry-run            show what would change; don’t write
  --name NAME              filename to target (default: carcols.meta)
  --clean-backups          ask to delete all carcols.meta.bak files
```
## Explanation

**Dry-run first (recommended)**
Run the `--dry-run` first to test if the script detects the carcols that you wish to normalize:

```bash
python script/normalize_carcols.py "DRIVE:\PATH-TO-FOLDER-CARS\data" --dry-run
```

***Apply changes**
After you are happy with the files the script parse, just commit to the changes and run the script normally :

```bash
python script/normalize_carcols.py "DRIVE:\PATH-TO-FOLDER-CARS\data"
```

**Clean up backups**
The script will create backups files for each carcols.meta it has modified. 
Review the files that has been modfied and if everything went ok, just remove the backup files: 

```bash
python script/normalize_carcols.py "DRIVE:\PATH-TO-FOLDER-CARS\data" --clean-backups
```

**Restore backups**
If you wish to restore all the backups file here is a quick method to do with powershell:
```ps1
Get-ChildItem -Recurse -Filter 'carcols.meta.bak' |
  ForEach-Object { Copy-Item $_.FullName ($_.FullName -replace '\.bak$','') -Force }
```

## Dev
```bash
ruff check .
black --check .
```

