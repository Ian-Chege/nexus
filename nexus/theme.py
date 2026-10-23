"""NEXUS SYSTEM MONITOR - theme engine.

Each theme is a full palette. Components receive a Theme object and recolour
themselves through apply_theme(); nothing relies on CustomTkinter's built-in
color themes, which keeps the neon look consistent across platforms.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constants import APP_NAME


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    appearance: str          # "Dark" or "Light" (passed to set_appearance_mode)
    # surfaces
    bg: str                  # window background
    sidebar: str             # sidebar background
    card: str                # card / graph background
    border: str              # card borders, separators
    # text
    text: str                # primary text
    muted: str               # secondary text
    # accents
    accent: str              # primary neon accent
    accent2: str             # secondary neon accent
    # semantic
    ok: str
    warning: str
    danger: str
    # graph extras
    grid: str                # graph grid lines
    track: str               # progress track / empty bars


THEMES: dict[str, Theme] = {
    # --- flagship ---------------------------------------------------------
    "nexus_dark": Theme(
        key="nexus_dark", name="Nexus Dark", appearance="Dark",
        bg="#0A0E17", sidebar="#0D1424", card="#131C2E", border="#22304F",
        text="#E8F1FF", muted="#7C8DB0",
        accent="#00E5FF", accent2="#39FF9C",
        ok="#39FF9C", warning="#FFB020", danger="#FF4D6D",
        grid="#1D2B47", track="#0F1626",
    ),
    # --- dark collection ---------------------------------------------------
    "cyberpunk": Theme(
        key="cyberpunk", name="Cyberpunk 2077", appearance="Dark",
        bg="#0B021C", sidebar="#120533", card="#180A3A", border="#33187C",
        text="#F3EFFF", muted="#9B8FC4",
        accent="#FF2BD6", accent2="#00F0FF",
        ok="#00FF9C", warning="#FFC857", danger="#FF3B5C",
        grid="#2A1266", track="#140734",
    ),
    "matrix": Theme(
        key="matrix", name="Matrix", appearance="Dark",
        bg="#030703", sidebar="#051005", card="#071807", border="#123F12",
        text="#C8FFD0", muted="#4E8A57",
        accent="#00FF41", accent2="#9DFFB8",
        ok="#00FF41", warning="#FFD24D", danger="#FF5555",
        grid="#0F2E0F", track="#041404",
    ),
    "synthwave": Theme(
        key="synthwave", name="Synthwave '84", appearance="Dark",
        bg="#150F2E", sidebar="#1C1440", card="#231852", border="#3D2A85",
        text="#F5EFFF", muted="#A291D4",
        accent="#FF71CE", accent2="#01CDFE",
        ok="#05F2A0", warning="#FFC24B", danger="#FF5C8A",
        grid="#31206D", track="#1A113E",
    ),
    "blood_moon": Theme(
        key="blood_moon", name="Blood Moon", appearance="Dark",
        bg="#0C0407", sidebar="#150709", card="#1B0A0E", border="#47182A",
        text="#FFE9EC", muted="#B07A85",
        accent="#FF2E4D", accent2="#FF9E3D",
        ok="#2ECC71", warning="#FFA34D", danger="#FF4D4D",
        grid="#3A1220", track="#170609",
    ),
    "midnight_gold": Theme(
        key="midnight_gold", name="Midnight Gold", appearance="Dark",
        bg="#0B0B0E", sidebar="#121218", card="#17171F", border="#32323F",
        text="#F5EFE0", muted="#97917E",
        accent="#FFD24D", accent2="#58E6D9",
        ok="#7DDE92", warning="#FFB84D", danger="#FF5A5A",
        grid="#2A2A36", track="#101015",
    ),
    "aurora": Theme(
        key="aurora", name="Aurora", appearance="Dark",
        bg="#06121A", sidebar="#0A1C26", card="#0E2530", border="#1B4A5C",
        text="#EAFBFF", muted="#7FA8B8",
        accent="#4DFFDF", accent2="#A78BFA",
        ok="#4DFFDF", warning="#FFC46B", danger="#FF6B81",
        grid="#153C4A", track="#0A1D26",
    ),
    # --- light collection ---------------------------------------------------
    "frost": Theme(
        key="frost", name="Frost (Light)", appearance="Light",
        bg="#EEF3F8", sidebar="#FFFFFF", card="#FFFFFF", border="#D7E1EC",
        text="#14283C", muted="#5E7186",
        accent="#0EA5E9", accent2="#10B981",
        ok="#10B981", warning="#D97706", danger="#E11D48",
        grid="#D3DEE9", track="#E4EBF2",
    ),
    "sakura": Theme(
        key="sakura", name="Sakura (Light)", appearance="Light",
        bg="#FBF7F9", sidebar="#FFFFFF", card="#FFFFFF", border="#EFDFE6",
        text="#3A2A33", muted="#8C7580",
        accent="#FF5C8A", accent2="#00B8A9",
        ok="#00B8A9", warning="#E8890C", danger="#E63950",
        grid="#EBD9E0", track="#F3E8EC",
    ),
}

DEFAULT_THEME = "nexus_dark"


def get_theme(key: str | None) -> Theme:
    """Return the theme registered under *key*, or the default theme."""
    if key in THEMES:
        return THEMES[key]
    return THEMES[DEFAULT_THEME]


def theme_names() -> list[str]:
    return [t.key for t in THEMES.values()]


def brand_initials(name: str) -> str:
    """Derive a short monogram from the app name (first letters, max 2)."""
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return APP_NAME[0]
    return "".join(p[0] for p in parts[:2]).upper()
