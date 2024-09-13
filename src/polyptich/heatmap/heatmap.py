import polyptich as pp
import matplotlib as mpl
from . import layouts

class Heatmap(pp.Grid):
    def __init__(
        self,
        data,
        col_layout=None,
        row_layout=None,
        obs = None,
        var = None,
        cmap="viridis",
        **kwargs,
    ):
        if col_layout is None:
            col_layout = layouts.Simple()
        if row_layout is None:
            row_layout = layouts.Simple()

        super().__init__(padding_width=col_layout.padding, padding_height=row_layout.padding)

        norm = mpl.colors.Normalize(vmin=data.min().min(), vmax=data.max().max())
        for j, name_row, data_row, row_height in row_layout.iter(data.T):
            for i, name_col, data_cell, col_width in col_layout.iter(data_row.T):
                ax = self[j, i] = pp.Panel((col_width, row_height))

                ax.matshow(data_cell.T, aspect="auto", cmap=cmap, norm = norm)
                ax.set_xticks([])
                ax.set_yticks([])
                