"""
TEP-HC publication figure style.

Typography and colours are aligned with site/index.html:
  --purple-deep #1C2E4A, --purple-dark #2C3E50, --purple-mid #5D6D7E,
  --magenta #1A5276, --purple-accent #84a3aa, --gray-purple #566573,
  --text-dark #17202A, body font Times New Roman.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt

# Manuscript site theme (site/index.html :root)
COLORS = {
    # CSS variable mapping
    "purple_deep": "#1C2E4A",
    "purple_dark": "#2C3E50",
    "purple_mid": "#5D6D7E",
    "purple_accent": "#84a3aa",
    "magenta": "#1A5276",
    "gray_purple": "#566573",
    "gray_light": "#EBEDEF",
    "text_dark": "#17202A",
    # Semantic aliases used in figure scripts
    "primary": "#1C2E4A",
    "accent": "#1A5276",
    "highlight": "#1A5276",
    "tep": "#1C2E4A",
    "observed": "#1C2E4A",
    "planck": "#1A5276",
    "model": "#2C3E50",
    "gr": "#5D6D7E",
    "lcdm": "#5D6D7E",
    "gray": "#566573",
    "light_gray": "#EBEDEF",
    "marginal": "#566573",
    "null": "#84a3aa",
    "info": "#566573",
    "text": "#17202A",
    "background": "#ffffff",
    "red": "#566573",       # rejected / contrast (theme grey-blue, not off-palette red)
    "shoes": "#495773",     # local-measurement series (doi-link grey-blue)
    "significant": "#1C2E4A",
    "fit": "#1A5276",
    "alt": "#1A5276",       # second regime / alternate series
    "border": "#5D6D7E",
    "grid": "#EBEDEF",
}

MANUSCRIPT_SERIF = ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif", "serif"]

FIG_SIZES = {
    "single_column": (3.5, 2.6),
    "double_column": (7.2, 4.5),
    "full_width": (10.0, 6.0),
    "web_standard": (7.5, 4.6),
    "web_tall": (7.5, 5.4),
    "web_two_panel": (7.5, 4.0),
    "web_quad": (7.5, 5.6),
}

FIG_EXPORT_SCALE = 1.65
FIG_EXPORT_DPI = 600

FIG_SIZE: Tuple[float, float] = FIG_SIZES["full_width"]


def export_figsize(name: str, *, scale: Optional[float] = None) -> Tuple[float, float]:
    """Return figsize (inches) scaled for high-resolution manuscript export."""
    s = FIG_EXPORT_SCALE if scale is None else scale
    w, h = FIG_SIZES[name]
    return (w * s, h * s)


def set_pub_style(
    scale: float = 1.0,
    dpi: int = FIG_EXPORT_DPI,
    transparent: bool = False,
) -> None:
    """Apply matplotlib rcParams matching the TEP-HC manuscript site."""
    plt.style.use("default")
    base_font = 9
    plt.rcParams.update(
        {
            "figure.figsize": export_figsize("full_width"),
            "font.family": "serif",
            "font.serif": MANUSCRIPT_SERIF,
            "mathtext.fontset": "stix",
            "mathtext.default": "it",
            "font.size": base_font * scale,
            "axes.labelsize": base_font * scale,
            "axes.titlesize": (base_font + 1) * scale,
            "xtick.labelsize": (base_font - 1) * scale,
            "ytick.labelsize": (base_font - 1) * scale,
            "legend.fontsize": (base_font - 1) * scale,
            "figure.titlesize": (base_font + 2) * scale,
            "figure.dpi": dpi,
            "savefig.dpi": dpi,
            "savefig.transparent": transparent,
            "figure.facecolor": COLORS["background"] if not transparent else "none",
            "axes.facecolor": COLORS["background"] if not transparent else "none",
            "axes.edgecolor": COLORS["border"],
            "axes.labelcolor": COLORS["text"],
            "axes.titlecolor": COLORS["purple_deep"],
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "text.color": COLORS["text"],
            "legend.frameon": True,
            "legend.framealpha": 0.95,
            "legend.facecolor": COLORS["background"],
            "legend.edgecolor": COLORS["border"],
            "savefig.facecolor": COLORS["background"] if not transparent else "none",
            "savefig.edgecolor": "none",
            "axes.grid": True,
            "grid.color": COLORS["grid"],
            "grid.linestyle": "-",
            "grid.linewidth": 0.4,
            "grid.alpha": 0.85,
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "lines.linewidth": 1.5,
            "lines.markersize": 5.5,
            "text.usetex": False,
        }
    )
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(
        color=[
            COLORS["purple_deep"],
            COLORS["magenta"],
            COLORS["purple_dark"],
            COLORS["purple_accent"],
            COLORS["gray_purple"],
        ]
    )


def save_fig(
    fig,
    path: Union[str, Path],
    *,
    dpi: int = FIG_EXPORT_DPI,
    tight: bool = True,
    close: bool = True,
    pad_inches: float = 0.04,
) -> Path:
    """Save a figure with consistent TEP export settings."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"dpi": dpi, "facecolor": COLORS["background"], "edgecolor": "none"}
    if tight:
        kwargs["bbox_inches"] = "tight"
        kwargs["pad_inches"] = pad_inches
    fig.savefig(out, **kwargs)
    if close:
        plt.close(fig)
    return out


def style_axes(
    ax,
    *,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
) -> None:
    """Apply consistent axis labels and light grid to a single axes."""
    if title:
        ax.set_title(title, pad=8, color=COLORS["purple_deep"])
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.85)
