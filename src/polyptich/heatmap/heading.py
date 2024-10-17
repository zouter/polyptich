import polyptich as pp
import matplotlib as mpl
import numpy as np
import pandas as pd


class Heading(pp.Grid):
    """
    Heading for multiple groups in a heatmap

    Parameters
    ----------
    data : pd.DataFrame
        Information about rows/columns
    info : pd.DataFrame
        Information about the different groups. Can contain columns:
        - label: the label to display
        - color: the color to use
    layout :
        Layout of the heatmap rows or columns
    margin : float
        Margin to use between the heatmap and the heading
    orientation : str
        Where to place the heading. Can be "top", "right", "bottom" or "left"


    """

    def __init__(
        self,
        data: pd.DataFrame,
        info: pd.DataFrame = None,
        layout=None,
        margin=None,
        orientation="top",
    ):
        if layout is None:
            layout = pp.heatmap.layouts.Simple()
        if orientation == "top":
            super().__init__(
                margin_bottom=layout.padding if margin is None else margin,
                padding_height=0.0,
                padding_width=layout.padding,
            )
        elif orientation == "right":
            super().__init__(
                margin_left=layout.padding if margin is None else margin,
                padding_width=0.0,
                padding_height=layout.padding,
            )
        elif orientation == "bottom":
            super().__init__(
                margin_top=layout.padding if margin is None else margin,
                padding_height=0.0,
                padding_width=layout.padding,
            )
        elif orientation == "left":
            super().__init__(
                margin_right=layout.padding if margin is None else margin,
                padding_width=0.0,
                padding_height=layout.padding,
            )
        print(layout)
        for i, name, df, width in layout.iter(data):
            if name is None:
                continue
            if info is None:
                label = name
                color = "black"
            else:
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
                color=color,
                alpha=0.5,
            )
            ax.add_patch(rect)
            ax.set_xticks([])
            ax.set_yticks([])
            if orientation in ["top", "bottom"]:
                text = ax.text(
                    0.5, 0.5, label, ha="center", va="center", fontsize=10, color="white"
                )
            elif orientation in ["right", "left"]:
                text = ax.text(
                    0.5,
                    0.5,
                    label,
                    ha="center",
                    va="center",
                    fontsize=10,
                    color="white",
                    rotation=90 if orientation == "left" else -90,
                )


class HeadingTop(Heading):
    __doc__ = Heading.__doc__

    def __init__(self, data, layout, info=None, margin=None):
        super().__init__(data, layout=layout, info=info, margin=margin, orientation="top")


class HeadingRight(Heading):
    __doc__ = Heading.__doc__

    def __init__(self, data, layout, info=None, margin=None):
        super().__init__(data, layout=layout, info=info, margin=margin, orientation="right")


class HeadingBottom(Heading):
    __doc__ = Heading.__doc__

    def __init__(self, data, layout, info=None, margin=None):
        super().__init__(data, layout=layout, info=info, margin=margin, orientation="bottom")


class HeadingLeft(Heading):
    __doc__ = Heading.__doc__

    def __init__(self, data, layout, info=None, margin=None):
        super().__init__(data, layout=layout, info=info, margin=margin, orientation="left")
