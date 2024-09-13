import polyptich as pp
import matplotlib as mpl


class Heading(pp.Grid):
    def __init__(self, data, info, layout = None, margin=None, orientation="top"):
        if layout is None:
            layout = pp.heatmap.layouts.Simple()
        if orientation == "top":
            super().__init__(
                margin_bottom=layout.padding if margin is None else margin, padding_height=0.0,  padding_width=layout.padding
            )
        elif orientation == "right":
            super().__init__(
                margin_left=layout.padding if margin is None else margin, padding_width=0.0,  padding_height=layout.padding
            )
        elif orientation == "bottom":
            super().__init__(
                margin_top=layout.padding if margin is None else margin, padding_height=0.0,  padding_width=layout.padding
            )
        elif orientation == "left":
            super().__init__(
                margin_right=layout.padding if margin is None else margin, padding_width=0.0,  padding_height=layout.padding
            )
        for i, name, df, width in layout.iter(data):
            if name is None:
                continue
            if name not in info.index:
                raise ValueError(f"Name {name} not found in info")
            if "label" in info.columns:
                label = info.loc[name]["label"]
            else:
                label = name
            if "color" in info.columns:
                color = info.loc[name]["color"]
            else:
                color = "black"

            if orientation == "top":
                ax = self[0, i] = pp.Panel((width, 0.2))
            elif orientation == "right":
                ax = self[i, 0] = pp.Panel((0.2, width))
            elif orientation == "bottom":
                ax = self[0, i] = pp.Panel((width, 0.2))
            elif orientation == "left":
                ax = self[i, 0] = pp.Panel((0.2, width))

            rect = mpl.patches.Rectangle(
                (0, 0),
                1,
                1,
                color = color,
                alpha=0.5,
            )
            ax.add_patch(rect)
            ax.set_xticks([])
            ax.set_yticks([])
            if orientation in ["top", "bottom"]:
                text = ax.text(0.5, 0.5, label, ha="center", va="center", fontsize=10, color="white")
            elif orientation in ["right", "left"]:
                text = ax.text(0.5, 0.5, label, ha="center", va="center", fontsize=10, color="white", rotation=90 if orientation == "left" else -90)

class HeadingTop(Heading):
    def __init__(self, data, layout, info, margin=0.):
        super().__init__(data, layout, info, margin=margin, orientation="top")

class HeadingRight(Heading):
    def __init__(self, data, layout, info, margin=0.):
        super().__init__(data, layout, info, margin=margin, orientation="right")

class HeadingBottom(Heading):
    def __init__(self, data, layout, info, margin=0.):
        super().__init__(data, layout, info, margin=margin, orientation="bottom")

class HeadingLeft(Heading):
    def __init__(self, data, layout, info, margin=0.):
        super().__init__(data, layout, info, margin=margin, orientation="left")