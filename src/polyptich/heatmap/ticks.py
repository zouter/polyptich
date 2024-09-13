import polyptich as pp
import matplotlib as mpl


class Ticks(pp.Grid):
    def __init__(self, data, layout, margin=0., orientation="top", size = 1.):
        if orientation == "top":
            super().__init__(
                margin_top=size, padding_height=0.0,  padding_width=layout.padding, margin_bottom = 0
            )
        elif orientation == "right":
            super().__init__(
                margin_left=size, padding_width=0.0,  padding_height=layout.padding, margin_right = 0
            )
        elif orientation == "bottom":
            super().__init__(
                margin_bottom=size, padding_height=0.0,  padding_width=layout.padding, margin_top = 0
            )
        elif orientation == "left":
            super().__init__(
                margin_left=size, padding_width=0.0,  padding_height=layout.padding, margin_right = 0
            )
        for i, name, df, width in layout.iter(data):
            if orientation == "top":
                ax = self[0, i] = pp.Panel((width, 0.01))
            elif orientation == "right":
                ax = self[i, 0] = pp.Panel((0.01, width))
            elif orientation == "bottom":
                ax = self[0, i] = pp.Panel((width, 0.01))
            elif orientation == "left":
                ax = self[i, 0] = pp.Panel((0.01, width))

            ax.axis("on")
            ax.set_xticks([])
            ax.set_yticks([])
            if orientation in ["top", "bottom"]:
                ax.set_xticks(range(df.shape[0]))
                label_kwargs = dict(rotation = 90, ha = "center", va = "top" if orientation == "bottom" else "bottom", fontsize = 10)
                ax.set_xticklabels(df.index, **label_kwargs)
                ax.set_xlim(-0.5, df.shape[0]-0.5)
            elif orientation in ["right", "left"]:
                ax.set_yticks(range(df.shape[0]))
                ax.set_yticklabels(df.index)
                ax.set_ylim(df.shape[0]-0.5, -0.5)
            for spine in ax.spines.values():
                spine.set_visible(False)

            if "color" in data.columns:
                for i, color in enumerate(df["color"]):
                    if orientation in ["top", "bottom"]:
                        ax.get_xticklabels()[i].set_color(color)
                    elif orientation in ["right", "left"]:
                        ax.get_yticklabels()[i].set_color(color)
        

class TicksLeft(Ticks):
    def __init__(self, data, layout, margin=0., size = 1):
        super().__init__(data, layout, margin = margin, orientation = "left", size = size)

class TicksRight(Ticks):
    def __init__(self, data, layout, margin=0., size = 1):
        super().__init__(data, layout, margin = margin, orientation = "right", size = size)
class TicksBottom(Ticks):
    def __init__(self, data, layout, margin=0., size = 1):
        super().__init__(data, layout, margin = margin, orientation = "bottom", size = size)

class TicksTop(Ticks):
    def __init__(self, data, layout, margin=0., size = 1):
        super().__init__(data, layout, margin = margin, orientation = "top", size = size)

# class SmartTicks():
#     def __init__(self, data, layout):
#         self.data = data
#         self.n_ticks = n_ticks
