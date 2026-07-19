"""
Color resolution for the NetForge terminal framework.

pyte reports foreground/background colors on each :class:`pyte.screens.Char`
as one of:

    * ``"default"``            -- the screen's default fg/bg
    * a named ANSI color       -- e.g. ``"red"``, ``"brightblue"``
    * a numeric string 0-255   -- an xterm 256-color palette index
    * a 6-digit hex string     -- a true color (24-bit) value

This module resolves any of those representations into a Qt-usable
``#RRGGBB`` hex string, using a dark-theme-friendly palette so the
terminal fits NetForge's overall dark UI.
"""

from __future__ import annotations

TERMINAL_BACKGROUND = "#1e1e1e"
TERMINAL_FOREGROUND = "#d4d4d4"
TERMINAL_CURSOR = "#ffffff"
TERMINAL_SELECTION = "#264f78"

# Standard 16-color ANSI palette, tuned for a dark background terminal.
_ANSI_16 = {
    "black": "#000000",
    "red": "#cd3131",
    "green": "#0dbc79",
    "brown": "#e5e510",
    "yellow": "#e5e510",
    "blue": "#2472c8",
    "magenta": "#bc3fbc",
    "cyan": "#11a8cd",
    "white": "#e5e5e5",
    "brightblack": "#666666",
    "brightred": "#f14c4c",
    "brightgreen": "#23d18b",
    "brightbrown": "#f5f543",
    "brightyellow": "#f5f543",
    "brightblue": "#3b8eea",
    "brightmagenta": "#d670d6",
    "brightcyan": "#29b8db",
    "brightwhite": "#e5e5e5",
}


def _build_256_palette() -> list[str]:
    """
    Build the standard xterm 256-color palette as a list of 256
    ``#RRGGBB`` hex strings, following the well known xterm layout:

        0-15    the basic + bright ANSI colors
        16-231  a 6x6x6 RGB color cube
        232-255 a 24-step grayscale ramp
    """
    palette: list[str] = []

    base_order = [
        "black", "red", "green", "brown", "blue",
        "magenta", "cyan", "white",
        "brightblack", "brightred", "brightgreen", "brightbrown",
        "brightblue", "brightmagenta", "brightcyan", "brightwhite",
    ]

    for name in base_order:
        palette.append(_ANSI_16[name])

    steps = [0, 95, 135, 175, 215, 255]

    for r in steps:
        for g in steps:
            for b in steps:
                palette.append("#{:02x}{:02x}{:02x}".format(r, g, b))

    for i in range(24):
        level = 8 + i * 10
        palette.append("#{:02x}{:02x}{:02x}".format(level, level, level))

    return palette


_PALETTE_256 = _build_256_palette()


def resolve_color(value: str, is_foreground: bool) -> str:
    """
    Resolve a pyte color value into a ``#RRGGBB`` hex string.

    :param value: the raw ``fg``/``bg`` value from a pyte ``Char``.
    :param is_foreground: whether this is being resolved for the
        foreground (affects the "default" fallback used).
    """

    if not value or value == "default":
        return TERMINAL_FOREGROUND if is_foreground else TERMINAL_BACKGROUND

    if value in _ANSI_16:
        return _ANSI_16[value]

    if value.isdigit():
        index = int(value)
        if 0 <= index < len(_PALETTE_256):
            return _PALETTE_256[index]
        return TERMINAL_FOREGROUND if is_foreground else TERMINAL_BACKGROUND

    if len(value) == 6:
        try:
            int(value, 16)
            return f"#{value}"
        except ValueError:
            pass

    return TERMINAL_FOREGROUND if is_foreground else TERMINAL_BACKGROUND
