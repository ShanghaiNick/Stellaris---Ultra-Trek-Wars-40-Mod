"""Measure the base game's weapon tech lines: which techs unlock weapons, and what depends on them."""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pdx

GAME = Path(sys.argv[1] if len(sys.argv) > 1 else r"F:\SteamLibrary\steamapps\common\Stellaris")

techs = {e.key: e for e in pdx.load_dir(GAME / "common" / "technology") if e.is_block}
print("techs:", len(techs))

comps = [e for e in pdx.load_dir(GAME / "common" / "component_templates") if e.is_block]
by_kind = defaultdict(int)
weapon_by_tech = defaultdict(list)
for c in comps:
    by_kind[c.key] += 1
    if c.key not in ("weapon_component_template", "strike_craft_component_template"):
        continue
    key = (pdx.field(c.body, "key") or "").strip('"')
    for t in pdx.str_list(pdx.field(c.body, "prerequisites")):
        weapon_by_tech[t].append(key)
print("component kinds:", dict(by_kind))
print("techs that unlock a weapon:", len(weapon_by_tech))

missing = [t for t in weapon_by_tech if t not in techs]
print("weapon prerequisites that are not techs in common/technology:", missing)

prereq = {k: pdx.str_list(pdx.field(e.body, "prerequisites")) for k, e in techs.items()}
weapon_techs = set(weapon_by_tech) & set(techs)

print("\n--- weapon techs: tier, area, category, start, file ---")
rows = []
for t in sorted(weapon_techs):
    b = techs[t].body
    rows.append((techs[t].path.name, pdx.field(b, "tier"), pdx.field(b, "area"),
                 (pdx.field(b, "category") or "").strip("{} "), pdx.field(b, "start_tech") or "no",
                 t, len(weapon_by_tech[t]), ",".join(prereq[t])))
for r in sorted(rows):
    print("  ".join(str(x) for x in r))

print("\n--- techs that are NOT weapon techs but require one ---")
for k, ps in sorted(prereq.items()):
    if k in weapon_techs:
        continue
    hit = [p for p in ps if p in weapon_techs]
    if hit:
        print(k, "<-", hit, "| file", techs[k].path.name)
