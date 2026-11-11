"""Measure every installed Workshop mod: what it replaces in the base game and where mods collide.

    python tools/scan_mods.py                       scan the Workshop folder, write docs/conflict_map.md
    python tools/scan_mods.py --workshop <folder>   another Workshop content folder

Reads loose files and zipped mods. Writes names and keys only, never mod content. Standard library only.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).parent))
import pdx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GAME = Path(r"F:\SteamLibrary\steamapps\common\Stellaris")
DEFAULT_WORKSHOP = Path(r"F:\SteamLibrary\steamapps\workshop\content\281990")

# folders whose top-level entries are named objects worth tracking: folder -> how to read the name
KEYED = {
    "common/technology": "entry",
    "common/ship_sizes": "entry",
    "common/graphical_culture": "entry",
    "common/component_templates": "key_field",
    "common/section_templates": "key_field",
    "common/governments/civics": "entry",
    "common/species_classes": "entry",
    "common/policies": "entry",
}
SCRIPT_ROOTS = ("common/", "events/", "map/", "prescripted_countries/", "interface/", "gfx/", "localisation/", "flags/", "music/", "sound/")
# marks of a mod that rebuilds the game rather than adding to it
CONVERSION_FILES = ("common/technology/", "common/ship_sizes/", "common/defines/", "common/buildings/", "common/pop_jobs/", "common/districts/")


def decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def mod_files(folder: Path):
    """Yield (posix relative path, reader) for every file of a mod, loose or zipped."""
    zips = list(folder.glob("*.zip"))
    loose = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() != ".zip"]
    for p in loose:
        yield p.relative_to(folder).as_posix(), (lambda p=p: p.read_bytes())
    for z in zips:
        try:
            zf = zipfile.ZipFile(z)
        except zipfile.BadZipFile:
            continue
        for info in zf.infolist():
            if not info.is_dir():
                yield str(PurePosixPath(info.filename)), (lambda zf=zf, info=info: zf.read(info))


def mod_name(folder: Path, files: dict) -> tuple[str, str]:
    for cand in ("descriptor.mod",):
        if cand in files:
            text = decode(files[cand]())
            name = re.search(r'^name\s*=\s*"([^"]*)"', text, re.M)
            ver = re.search(r'^supported_version\s*=\s*"([^"]*)"', text, re.M)
            return (name.group(1) if name else folder.name, ver.group(1) if ver else "?")
    return folder.name, "?"


def object_keys(text: str, how: str) -> list[str]:
    try:
        ents = pdx.entries(text)
    except ValueError:
        return []
    out = []
    for e in ents:
        if not e.is_block or e.key.startswith("@"):
            continue
        if how == "entry":
            out.append(e.key)
        else:
            k = pdx.field(e.body, "key")
            if k:
                out.append(k.strip('"'))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--workshop", type=Path, default=DEFAULT_WORKSHOP)
    args = ap.parse_args()

    vanilla_files = {p.relative_to(args.game).as_posix().lower()
                     for root in ("common", "events", "map", "prescripted_countries", "interface")
                     for p in (args.game / root).rglob("*") if p.is_file()}
    vanilla_keys: dict[str, set[str]] = {}
    for folder, how in KEYED.items():
        keys = set()
        for f in (args.game / folder).glob("*.txt"):
            keys.update(object_keys(pdx.read_text(f), how))
        vanilla_keys[folder] = keys

    mods = []
    owners: dict[tuple[str, str], list[str]] = defaultdict(list)      # (folder, key) -> mod names
    file_owners: dict[str, list[str]] = defaultdict(list)             # vanilla file replaced -> mod names
    for folder in sorted(p for p in args.workshop.iterdir() if p.is_dir()):
        files = dict(mod_files(folder))
        if not files:
            mods.append({"id": folder.name, "name": folder.name, "empty": True})
            continue
        name, ver = mod_name(folder, files)
        label = f"{name} ({folder.name})"
        replaced = sorted(f for f in files if f.lower() in vanilla_files)
        for f in replaced:
            file_owners[f.lower()].append(label)
        new_keys, overridden = defaultdict(list), defaultdict(list)
        for rel, read in files.items():
            low = rel.lower()
            if not low.endswith(".txt"):
                continue
            for kfolder, how in KEYED.items():
                if low.startswith(kfolder + "/") and low.count("/") == kfolder.count("/") + 1:
                    for k in object_keys(decode(read()), how):
                        owners[(kfolder, k)].append(label)
                        (overridden if k in vanilla_keys[kfolder] else new_keys)[kfolder].append(k)
        touched = sorted({c for c in CONVERSION_FILES if any(f.lower().startswith(c) for f in files)})
        kinds = defaultdict(int)
        for f in files:
            kinds[f.split("/", 1)[0].lower() if "/" in f else "(root)"] += 1
        mods.append({
            "id": folder.name, "name": name, "supported_version": ver, "files": len(files),
            "replaces_vanilla_files": replaced,
            "overrides_vanilla_objects": {k: sorted(set(v)) for k, v in overridden.items()},
            "adds": {k: len(set(v)) for k, v in new_keys.items()},
            "graphical_cultures": sorted(set(new_keys.get("common/graphical_culture", []))),
            "ship_sizes": sorted(set(new_keys.get("common/ship_sizes", []))),
            "top_folders": dict(sorted(kinds.items())),
            "gameplay_folders": touched,
        })

    collisions = {f"{k[0]}::{k[1]}": sorted(set(v)) for k, v in owners.items() if len(set(v)) > 1}
    shared_files = {f: sorted(set(v)) for f, v in file_owners.items() if len(set(v)) > 1}

    out_dir = ROOT / "docs"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "conflict_map.json").write_text(json.dumps(
        {"mods": mods, "object_collisions": collisions, "vanilla_files_replaced_by_several": shared_files}, indent=1),
        encoding="utf-8", newline="\n")

    md = io.StringIO()
    real = [m for m in mods if not m.get("empty")]
    md.write(f"# Conflict map\n\nGenerated by `tools/scan_mods.py`. {len(real)} mods read"
             f" ({len(mods) - len(real)} folders empty), game at `{args.game}`.\n\n")
    md.write("## Each mod\n\n| Mod | For version | Files | Base-game files replaced | Base-game objects redefined | New techs | New ship sizes | Ship looks |\n|---|---|---|---|---|---|---|---|\n")
    for m in sorted(real, key=lambda m: -len(m["replaces_vanilla_files"])):
        md.write(f"| {m['name']} ({m['id']}) | {m['supported_version']} | {m['files']} | {len(m['replaces_vanilla_files'])} | "
                 f"{sum(len(v) for v in m['overrides_vanilla_objects'].values())} | {m['adds'].get('common/technology', 0)} | "
                 f"{m['adds'].get('common/ship_sizes', 0)} | {len(m['graphical_cultures'])} |\n")
    md.write("\n## Base-game files replaced by more than one mod\n\nOnly one mod's copy of each file can load.\n\n")
    for f, who in sorted(shared_files.items()):
        md.write(f"- `{f}`: " + "; ".join(who) + "\n")
    if not shared_files:
        md.write("None.\n")
    md.write("\n## Objects defined by more than one mod\n\n")
    by_folder = defaultdict(list)
    for k, who in collisions.items():
        by_folder[k.split("::")[0]].append((k.split("::")[1], who))
    for folder, items in sorted(by_folder.items()):
        md.write(f"### {folder} ({len(items)})\n\n")
        pairs = defaultdict(list)
        for key, who in items:
            pairs[" + ".join(who)].append(key)
        for who, keys in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
            sample = ", ".join(sorted(keys)[:8]) + (" ..." if len(keys) > 8 else "")
            md.write(f"- **{len(keys)}** shared by {who}: {sample}\n")
        md.write("\n")
    if not collisions:
        md.write("None.\n")
    (out_dir / "conflict_map.md").write_text(md.getvalue(), encoding="utf-8", newline="\n")

    print(f"mods read: {len(real)}; empty folders: {len(mods) - len(real)}")
    print(f"base-game files replaced by several mods: {len(shared_files)}")
    print(f"objects defined by several mods: {len(collisions)}")
    print("wrote", out_dir / "conflict_map.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
