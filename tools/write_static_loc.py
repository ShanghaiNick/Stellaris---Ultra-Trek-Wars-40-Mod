"""Write the hand-authored English text (research focus policies). Kept as a script so the file always
has the byte-order mark and layout the game requires."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

AREAS = {
    "physics": ("Physics Research Focus", "Choose which branch of physics our scientists pursue. The chosen field appears among our research options far more often."),
    "society": ("Society Research Focus", "Choose which branch of society research our scientists pursue. The chosen field appears among our research options far more often."),
    "engineering": ("Engineering Research Focus", "Choose which branch of engineering our scientists pursue. The chosen field appears among our research options far more often."),
}
OPTIONS = {
    "physics_none": ("Balanced", "No field is favored. Research options are drawn at their normal chances."),
    "society_none": ("Balanced", "No field is favored. Research options are drawn at their normal chances."),
    "engineering_none": ("Balanced", "No field is favored. Research options are drawn at their normal chances."),
    "particles": ("Particles", "Energy weapons, reactors and power generation."),
    "field_manipulation": ("Field Manipulation", "Shields, energy production and exotic fields."),
    "computing": ("Computing", "Sensors, research, point-defense tracking and artificial intelligence."),
    "biology": ("Biology", "Food, genetics, growth and living ships."),
    "military_theory": ("Military Theory", "Fleet size, armies, doctrines and command."),
    "new_worlds": ("New Worlds", "Colonization, terraforming and habitability."),
    "statecraft": ("Statecraft", "Government, diplomacy, unity and administration."),
    "psionics": ("Psionics", "The powers of the mind and the Shroud."),
    "archaeostudies": ("Archaeostudies", "The relics and weapons of vanished civilizations."),
    "propulsion": ("Propulsion", "Kinetic weapons, missiles, torpedoes, thrusters and drives."),
    "voidcraft": ("Voidcraft", "Ship hulls, starbases, strike craft and megastructures."),
    "materials": ("Materials", "Armor, mining, alloys and construction."),
    "industry": ("Industry", "Factories, robotics and production."),
}

lines = ["l_english:"]
for area, (name, desc) in AREAS.items():
    lines.append(f' policy_utw_{area}_focus:0 "{name}"')
    lines.append(f' policy_utw_{area}_focus_desc:0 "{desc}"')
for key, (name, desc) in OPTIONS.items():
    lines.append(f' utw_focus_{key}:0 "{name}"')
    lines.append(f' utw_focus_{key}_name:0 "{name}"')
    lines.append(f' utw_focus_{key}_desc:0 "{desc}"')

out = ROOT / "mod" / "localisation" / "english" / "utw_static_l_english.yml"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\n")
print("wrote", out, len(lines) - 1, "keys")
