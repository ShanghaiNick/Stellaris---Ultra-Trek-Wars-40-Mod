# Starhammer

A Stellaris mod for one giant crossover galaxy: Star Trek, Star Wars, Warhammer 40,000 and more, each
with its own technology tree, playing in the same game as the base-game empires.

Built for Stellaris 4.5. Version 0.2.2. Loads and starts a game with 78 Workshop mods; long play is untested.

## What it does today

- **A separate weapon tree per franchise.** Pick the *Final Frontier* (Star Trek) or *A Galaxy Far, Far Away*
  (Star Wars) origin and your empire researches its own weapon lines: 48 technologies and 83 weapons each,
  from Phase Cannons to Transphasic Torpedoes, from Laser Cannons to the Composite Superlaser. Base-game
  weapon lines above the starting tier stop appearing as research options for those empires. Base-game
  empires keep the normal tree and never roll franchise weapons.
- **Salvage still works by design.** Franchise techs are hidden by weight, not by a hard lock, so tech
  gained from debris is meant to stay available. Unverified in play.
- **More choice in research.**
  - Six research options per area instead of three.
  - Three new policies (Physics, Society and Engineering Research Focus), open to every empire from day
    one. Pick a field and it is drawn at four times its normal weight.

Franchise weapons currently share the base game's stats (with small per-franchise adjustments), icons,
effects and descriptions. Ship models, portraits and flags come from the shipset mods on the Workshop;
this mod does not include or copy them.

## Layout

| Folder | What |
|---|---|
| `mod/` | The mod itself. Point a `.mod` file's `path=` at this folder. |
| `data/core_lines.json` | The base-game weapon lines every franchise gets a copy of. |
| `data/franchises/*.json` | One file per franchise: names, origin text, stat adjustments. |
| `tools/build.py` | Generates the franchise trees from the installed game. |
| `tools/scan_mods.py` | Reads every installed Workshop mod and writes a conflict map. |
| `tools/pdx.py` | Small reader for Paradox script files. |

## Building

Needs Python 3.10 or newer, no packages.

```
python tools/build.py --game "<path to Stellaris>"
python tools/write_static_loc.py
```

`build.py` reads the game's own technology, component and stat files and writes everything named
`utw_generated` under `mod/`, plus patched copies of the seven base-game technology files it has to
change. After a game patch, run it again.

## Adding a franchise

Copy a file in `data/franchises/`, change `id`, `prefix`, the origin text and the names, and rebuild.

## Known limits

- Replaces seven base-game technology files (`00_phys_weapon_tech.txt`, `00_eng_weapon_tech.txt`,
  `00_eng_tech.txt`, `00_nomads_dlc_tech.txt` and the three repeatable files). A mod that replaces the
  same files will conflict; load this one after it and rebuild against it if needed.
- Technologies from other mods that require a base-game weapon tech do not yet accept the franchise copy.
- Random AI empires do not pick the franchise origins yet. Prescripted franchise empires are next.

## Credits and rights

Star Trek, Star Wars, Warhammer 40,000 and the other settings named here belong to their owners. This is
a free fan project with no affiliation. Stellaris belongs to Paradox Interactive. No other modder's
files are included in this repository.
