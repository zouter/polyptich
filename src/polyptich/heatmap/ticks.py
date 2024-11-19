import polyptich as pp
import matplotlib as mpl
import numpy as np


class Ticks(pp.Grid):
    def __init__(self, data, layout = None, margin=0., orientation="top", size = 1., label_column = "label", fontsize = 10):
        data = data.copy()
        if layout is None:
            layout = pp.heatmap.layouts.Simple()
        if orientation == "top":
            super().__init__(
                margin_top=size, padding_height=0.0,  padding_width=layout.padding, margin_bottom = 0,
            )
        elif orientation == "right":
            super().__init__(
                margin_right=size, padding_width=0.0,  padding_height=layout.padding, margin_left = 0
            )
        elif orientation == "bottom":
            super().__init__(
                margin_bottom=size, padding_height=0.0,  padding_width=layout.padding, margin_top = 0
            )
        elif orientation == "left":
            super().__init__(
                margin_left=size, padding_width=0.0,  padding_height=layout.padding, margin_right = 0
            )

        if label_column not in data.columns:
            data[label_column] = data.index

        if "tick" not in data.columns:
            data["tick"] = True
        
        for i, name, df, width in layout.iter(data):
            if orientation == "top":
                ax = self[0, i] = pp.Panel((width, 0.01))
            elif orientation == "right":
                ax = self[i, 0] = pp.Panel((0.01, width))
            elif orientation == "bottom":
                ax = self[0, i] = pp.Panel((width, 0.01))
            elif orientation == "left":
                ax = self[i, 0] = pp.Panel((0.01, width))

            df["ix"] = np.arange(df.shape[0])
            df_oi = df.loc[df["tick"]]

            ax.axis("on")
            ax.set_xticks([])
            ax.set_yticks([])
            label_kwargs = dict(fontsize = fontsize)
            if orientation in ["top", "bottom"]:
                label_kwargs = {
                    "rotation": 90,
                    "ha": "center",
                    "va": "top" if orientation == "bottom" else "bottom",
                    **label_kwargs
                }

                ax.set_xticks(df_oi["ix"])
                ax.set_xticklabels(df_oi[label_column], **label_kwargs)
                ax.set_xlim(-0.5, df.shape[0]-0.5)

                ax.tick_params(axis = "x", size = 2, pad = 2)

                if orientation == "top":
                    ax.xaxis.tick_top()

            elif orientation in ["right", "left"]:
                ax.set_yticks(df_oi["ix"])
                label_kwargs = {
                    "rotation": 0,
                    "ha": "left" if orientation == "right" else "right",
                    "va": "center",
                    **label_kwargs
                }
                ax.set_yticklabels(df_oi[label_column], **label_kwargs)
                ax.set_ylim(df.shape[0]-0.5, -0.5)
                ax.tick_params(axis = "y", size = 2, pad = 2)


                # ax.tick_params(axis = "y", size = 0)

                # ax.set_yticks(np.arange(df.shape[0])-0.5, minor = True)
                # ax.tick_params(axis = "y", which = "minor", size = 5)

                if orientation == "right":
                    ax.yaxis.tick_right()

            for spine in ax.spines.values():
                spine.set_visible(False)

            if "color" in data.columns:
                for i, color in enumerate(df["color"]):
                    if orientation in ["top", "bottom"]:
                        ax.get_xticklabels()[i].set_color(color)
                    elif orientation in ["right", "left"]:
                        ax.get_yticklabels()[i].set_color(color)
        

class TicksLeft(Ticks):
    def __init__(self, data, layout = None, margin=0., size = 1, **kwargs):
        super().__init__(data, layout, margin = margin, orientation = "left", size = size, **kwargs)

class TicksRight(Ticks):
    def __init__(self, data, layout = None, margin=0., size = 1, **kwargs):
        super().__init__(data, layout, margin = margin, orientation = "right", size = size, **kwargs)
class TicksBottom(Ticks):
    def __init__(self, data, layout = None, margin=0., size = 1, **kwargs):
        super().__init__(data, layout, margin = margin, orientation = "bottom", size = size, **kwargs)

class TicksTop(Ticks):
    def __init__(self, data, layout = None, margin=0., size = 1, **kwargs):
        super().__init__(data, layout, margin = margin, orientation = "top", size = size, **kwargs)

# class SmartTicks():
#     def __init__(self, data, layout):
#         self.data = data
#         self.n_ticks = n_ticks
