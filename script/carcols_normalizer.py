# SPDX-License-Identifier: MIT
"""
carcols_normalizer.py

Normalize runs of <Item>...</Item> blocks in carcols.meta by <type>, replacing each run with
exactly four standardized <Item> entries (modifier values 25, 50, 75, 100). Creates a .bak
backup before modifying any file. Includes an interactive backup cleaner.
"""

import argparse
import re
import shutil
from pathlib import Path  # <-- keep it here


# Match each <Item>...</Item> block; capture leading indentation and the inner XML.
ITEM_RE = re.compile(r"(?ims)(^[ \t]*)<Item\b[^>]*>(.*?)</Item>")
# Grab the <type>...</type> value if present.
TYPE_RE = re.compile(r"(?is)<type>\s*([^<]+)\s*</type>")


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def clean_backups(root: Path) -> int:
    """
    Find and (optionally) delete all 'carcols.meta.bak' files under root.
    Returns how many files were deleted.
    """
    baks = sorted(p for p in root.rglob("carcols.meta.bak") if p.is_file())
    if not baks:
        print("No backup files found.")
        return 0

    total_bytes = sum(p.stat().st_size for p in baks)
    print(f"Found {len(baks)} backup file(s), total {_human_size(total_bytes)}.")
    for p in baks:
        print(f"  - {p}")
    ans = input("Delete them now? [y/N] ").strip().lower()
    if ans not in ("y", "yes"):
        print("Skipping deletion.")
        return 0

    deleted = 0
    for p in baks:
        try:
            p.unlink()
            deleted += 1
        except Exception as e:
            print(f"Could not delete {p}: {e}")

    print(f"Deleted {deleted} backup file(s).")
    return deleted


def build_items(indent: str, vtype: str) -> str:
    """Render four standardized <Item> blocks with modifiers 25/50/75/100."""
    out = []
    for val in (25, 50, 75, 100):
        out.append(
            f"{indent}<Item>\n"
            f"{indent}  <identifier />\n"
            f"{indent}  <modifier value=\"{val}\" />\n"
            f"{indent}  <audioApply value=\"1.000000\" />\n"
            f"{indent}  <weight value=\"0\" />\n"
            f"{indent}  <type>{vtype}</type>\n"
            f"{indent}</Item>\n"
        )
    return "".join(out)


def scan_items(text: str):
    """Yield (start, end, indent, vtype or None) for each <Item> block."""
    for m in ITEM_RE.finditer(text):
        indent, inner = m.group(1), m.group(2)
        tm = TYPE_RE.search(inner)
        vtype = tm.group(1).strip() if tm else None
        yield (m.start(), m.end(), indent, vtype)


def main():
    ap = argparse.ArgumentParser(
        description="Normalize consecutive <Item> runs in carcols.meta files."
    )
    ap.add_argument(
        "root",
        nargs="?",
        default=".",
        help="root folder to scan (default: current directory)",
    )
    ap.add_argument(
        "--any",
        action="store_true",
        help="operate on ANY VMT_* type (not only gearbox/brakes/engine)",
    )
    ap.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="show what would change; do not write files",
    )
    ap.add_argument(
        "--name",
        default="carcols.meta",
        help="filename to target (default: carcols.meta)",
    )
    ap.add_argument(
        "--clean-backups",
        action="store_true",
        help="scan for 'carcols.meta.bak' under ROOT and ask to delete them",
    )
    args = ap.parse_args()

    root = Path(args.root)
    if args.clean_backups:
        clean_backups(root)
        return

    targets = {"VMT_GEARBOX", "VMT_BRAKES", "VMT_ENGINE"}
    updated = 0

    for meta in root.rglob(args.name):
        try:
            text = meta.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = meta.read_text(encoding="latin-1", errors="replace")

        items = list(scan_items(text))
        if not items:
            print(f"No <Item> blocks in {meta}")
            continue

        # Group consecutive same-type items (only whitespace allowed between them)
        groups, i = [], 0
        while i < len(items):
            s, e, indent, vtype = items[i]
            if not vtype or not vtype.upper().startswith("VMT_"):
                i += 1
                continue
            vt = vtype.upper()
            if not args.any and vt not in targets:
                i += 1
                continue

            j = i + 1
            group_start, group_end, group_indent = s, e, indent
            while j < len(items):
                s2, e2, _, vtype2 = items[j]
                between = text[group_end:s2]
                if (
                    vtype2
                    and vtype2.strip().upper() == vt
                    and re.fullmatch(r"\s*", between, re.S)
                ):
                    group_end = e2
                    j += 1
                else:
                    break

            groups.append((group_start, group_end, group_indent, vt))
            i = j

        if not groups:
            print(f"No matching VMT items in {meta}")
            continue

        # Apply replacements
        new_parts, pos = [], 0
        for s, e, indent, vtype in groups:
            new_parts.append(text[pos:s])
            new_parts.append(build_items(indent, vtype))
            pos = e
        new_parts.append(text[pos:])
        new_text = "".join(new_parts)

        if args.dry_run:
            print(f"[DRY] {meta}  -> would replace {len(groups)} run(s)")
            continue

        shutil.copy2(meta, meta.with_suffix(meta.suffix + ".bak"))
        meta.write_text(new_text, encoding="utf-8")
        print(f"Updated {meta}  (replaced {len(groups)} run(s))")
        updated += 1

    print(f"\nDone. Files updated: {updated}")


if __name__ == "__main__":
    main()
