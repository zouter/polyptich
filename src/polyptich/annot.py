import matplotlib.patheffects as patheffects

def annotate_corner(ax, text, loc="tl", fontsize=6, box=False, ec = "white", offset = 1, **kwargs):
    """
    Annotate text in a specified corner or region of an Axes.

    Parameters:
    - ax: The matplotlib Axes object.
    - text: The annotation string.
    - loc: Position code, one of:
        'tl', 'tr', 'bl', 'br', 'tc', 'bc', 'cl', 'cr', 'cc'
    - fontsize: Font size for text.
    - box: If True, draws a semi-transparent background box.
    - **kwargs: Additional styling passed to ax.annotate().
    """
    loc = loc.lower()
    positions = {
        "tl": ((0.01, 0.99), "left", "top"),
        "tr": ((0.99, 0.99), "right", "top"),
        "bl": ((0.01, 0.01), "left", "bottom"),
        "br": ((0.99, 0.01), "right", "bottom"),
        "tc": ((0.5, 0.99), "center", "top"),
        "bc": ((0.5, 0.01), "center", "bottom"),
        "cl": ((0.01, 0.5), "left", "center"),
        "cr": ((0.99, 0.5), "right", "center"),
        "cc": ((0.5, 0.5), "center", "center"),
    }

    offsets = {
        "tl": (offset, -offset),
        "tr": (-offset, -offset),
        "bl": (offset, offset),
        "br": (-offset, offset),
        "tc": (0, -offset),
        "bc": (0, offset),
        "cl": (offset, 0),
        "cr": (-offset, 0),
        "cc": (0, 0),
    }

    if loc not in positions:
        raise ValueError(f"Invalid location code '{loc}'. Use one of: {', '.join(positions.keys())}")

    (xy, ha, va) = positions[loc]
    offset = offsets[loc]

    text_obj = ax.annotate(
        text,
        xy=xy,
        xycoords="axes fraction",
        textcoords="offset points",
        xytext=offset,
        ha=ha,
        va=va,
        fontsize=fontsize,
        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=1) if box else None,
        **kwargs
    )

    text_obj.set_path_effects([
        patheffects.Stroke(linewidth=2, foreground=ec, alpha = 0.5),
        patheffects.Stroke(linewidth=1, foreground=ec),
        patheffects.Normal(),
    ])